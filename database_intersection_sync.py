#!/usr/bin/env python3
"""
Database Intersection Sync
==========================
Sincronizează datele între două baze de date diferite, găsind intersecțiile
și rezolvând inconsistențele între tabelele corespondente.
"""

import sqlite3
import json
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class Record:
    """Reprezintă o înregistrare din baza de date"""
    id: int
    name: str
    email: str
    phone: str
    last_updated: str
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self.calculate_checksum()

    def calculate_checksum(self) -> str:
        """Calculează checksum pentru detectarea modificărilor"""
        data = f"{self.name}|{self.email}|{self.phone}|{self.last_updated}"
        return hashlib.md5(data.encode()).hexdigest()

class DatabaseIntersectionSync:
    """Sincronizează datele între două baze de date SQLite"""
    
    def __init__(self, source_db: str, target_db: str):
        self.source_db = source_db
        self.target_db = target_db
        self.sync_log = []
    
    def create_sample_databases(self):
        """Creează baze de date de exemplu pentru testare"""
        
        # Baza de date sursă (sistem vechi)
        conn1 = sqlite3.connect(self.source_db)
        conn1.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Date vechi cu probleme
        sample_data = [
            (1, "Ion Popescu", "ion.popescu@email.com", "0712345678", "2023-01-15"),
            (2, "Maria Ionescu", "maria.ionescu@gmail.com", "0798765432", "2023-02-20"),
            (3, "Andrei Dumitrescu", "andrei.dumitrescu@yahoo.com", "0723456789", "2023-03-10"),
            (4, "Elena Vasilescu", "elena.vasilescu@outlook.com", "0734567890", "2023-04-05"),
        ]
        
        conn1.executemany(
            "INSERT OR REPLACE INTO users (id, name, email, phone, last_updated) VALUES (?, ?, ?, ?, ?)",
            sample_data
        )
        conn1.commit()
        conn1.close()
        
        # Baza de date țintă (sistem nou)
        conn2 = sqlite3.connect(self.target_db)
        conn2.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Date noi parțial sincronizate
        new_data = [
            (1, "Ion Popescu", "ion.popescu@email.ro", "0712345678", "2023-12-01"),  # Email modificat
            (2, "Maria Ionescu", "maria.ionescu@gmail.com", "0798765432", "2023-02-20"),  # Identică
            (5, "Nou Utilizator", "nou@email.com", "0745678901", "2023-12-01"),  # Nou
        ]
        
        conn2.executemany(
            "INSERT OR REPLACE INTO users (id, name, email, phone, last_updated) VALUES (?, ?, ?, ?, ?)",
            new_data
        )
        conn2.commit()
        conn2.close()
    
    def scan_intersections(self) -> Dict[str, List[Record]]:
        """Scanează intersecțiile între cele două baze de date"""
        print("🔍 Scanare intersecții între baze de date...")
        
        source_records = self._load_records(self.source_db)
        target_records = self._load_records(self.target_db)
        
        # Găsește intersecțiile
        source_ids = {r.id for r in source_records}
        target_ids = {r.id for r in target_records}
        
        intersection_ids = source_ids & target_ids
        only_source = source_ids - target_ids
        only_target = target_ids - source_ids
        
        print(f"   📊 Total în sursă: {len(source_records)}")
        print(f"   📊 Total în țintă: {len(target_records)}")
        print(f"   🔗 Intersecție (ID-uri comune): {len(intersection_ids)}")
        print(f"   ➡️  Doar în sursă: {len(only_source)}")
        print(f"   ⬅️  Doar în țintă: {len(only_target)}")
        
        return {
            "source_only": [r for r in source_records if r.id in only_source],
            "target_only": [r for r in target_records if r.id in only_target],
            "intersection": {
                r.id: {
                    "source": next(r for r in source_records if r.id == r.id),
                    "target": next(r for r in target_records if r.id == r.id)
                } for r in source_records if r.id in intersection_ids
            }
        }
    
    def detect_conflicts(self, intersections: Dict) -> List[Dict]:
        """Detectează conflictele în intersecțiile găsite"""
        print("\n⚠️  Detectare conflicte în intersecții...")
        
        conflicts = []
        for record_id, pair in intersections["intersection"].items():
            source_record = pair["source"]
            target_record = pair["target"]
            
            # Verifică dacă sunt identice
            if source_record.checksum != target_record.checksum:
                conflict = {
                    "id": record_id,
                    "source": source_record,
                    "target": target_record,
                    "fields_changed": self._get_changed_fields(source_record, target_record)
                }
                conflicts.append(conflict)
                
                print(f"   ⚠️  Conflict ID {record_id}:")
                for field in conflict["fields_changed"]:
                    print(f"      {field}: '{source_record.__dict__[field]}' vs '{target_record.__dict__[field]}'")
        
        print(f"   📋 Total conflicte: {len(conflicts)}")
        return conflicts
    
    def sync_intersections(self, intersections: Dict, strategy: str = "source_wins") -> Dict[str, int]:
        """Sincronizează intersecțiile conform strategiei alese"""
        print(f"\n🔄 Sincronizare intersecții (strategie: {strategy})...")
        
        stats = {"updated": 0, "inserted": 0, "errors": 0}
        
        # 1. Sincronizează conflictele din intersecție
        for record_id, pair in intersections["intersection"].items():
            source_record = pair["source"]
            target_record = pair["target"]
            
            if source_record.checksum != target_record.checksum:
                try:
                    if strategy == "source_wins":
                        self._update_record(self.target_db, source_record)
                    elif strategy == "target_wins":
                        self._update_record(self.source_db, target_record)
                    elif strategy == "latest_wins":
                        latest = source_record if source_record.last_updated > target_record.last_updated else target_record
                        if latest == source_record:
                            self._update_record(self.target_db, source_record)
                        else:
                            self._update_record(self.source_db, target_record)
                    
                    stats["updated"] += 1
                    self.sync_log.append(f"Updated record ID {record_id}")
                    
                except Exception as e:
                    stats["errors"] += 1
                    self.sync_log.append(f"Error updating ID {record_id}: {e}")
        
        # 2. Inserează înregistrările doar din sursă în țintă
        for record in intersections["source_only"]:
            try:
                self._insert_record(self.target_db, record)
                stats["inserted"] += 1
                self.sync_log.append(f"Inserted new record ID {record.id}")
            except Exception as e:
                stats["errors"] += 1
                self.sync_log.append(f"Error inserting ID {record.id}: {e}")
        
        return stats
    
    def generate_sync_report(self, intersections: Dict, conflicts: List, stats: Dict):
        """Generează raportul de sincronizare"""
        print("\n" + "="*60)
        print("📋 RAPORT SINCRONIZARE BAZE DE DATE")
        print("="*60)
        
        print(f"📊 Statistici intersecții:")
        print(f"   • Total înregistrări în sursă: {len(intersections['source_only']) + len(intersections['intersection'])}")
        print(f"   • Total înregistrări în țintă: {len(intersections['target_only']) + len(intersections['intersection'])}")
        print(f"   • Intersecții găsite: {len(intersections['intersection'])}")
        print(f"   • Conflicte detectate: {len(conflicts)}")
        
        print(f"\n🔄 Acțiuni efectuate:")
        print(f"   • Înregistrări actualizate: {stats['updated']}")
        print(f"   • Înregistrări inserate: {stats['inserted']}")
        print(f"   • Erori: {stats['errors']}")
        
        if self.sync_log:
            print(f"\n📝 Log detaliat:")
            for entry in self.sync_log[-10:]:  # Ultimele 10 intrări
                print(f"   • {entry}")
    
    def _load_records(self, db_path: str) -> List[Record]:
        """Încarcă înregistrările din baza de date"""
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT id, name, email, phone, last_updated FROM users")
        
        records = []
        for row in cursor.fetchall():
            record = Record(
                id=row[0],
                name=row[1],
                email=row[2],
                phone=row[3],
                last_updated=row[4]
            )
            records.append(record)
        
        conn.close()
        return records
    
    def _get_changed_fields(self, source: Record, target: Record) -> List[str]:
        """Identifică câmpurile care au fost modificate"""
        changed = []
        for field in ["name", "email", "phone", "last_updated"]:
            if getattr(source, field) != getattr(target, field):
                changed.append(field)
        return changed
    
    def _update_record(self, db_path: str, record: Record):
        """Actualizează o înregistrare în baza de date"""
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE users SET name=?, email=?, phone=?, last_updated=? WHERE id=?",
            (record.name, record.email, record.phone, record.last_updated, record.id)
        )
        conn.commit()
        conn.close()
    
    def _insert_record(self, db_path: str, record: Record):
        """Inserează o înregistrare în baza de date"""
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT OR REPLACE INTO users (id, name, email, phone, last_updated) VALUES (?, ?, ?, ?, ?)",
            (record.id, record.name, record.email, record.phone, record.last_updated)
        )
        conn.commit()
        conn.close()

def main():
    """Funcția principală pentru testarea sincronizării"""
    print("🗄️  DATABASE INTERSECTION SYNC")
    print("="*50)
    
    # Inițializează sincronizatorul
    sync = DatabaseIntersectionSync("source_database.db", "target_database.db")
    
    # Creează bazele de date de exemplu
    print("1. Creare baze de date de exemplu...")
    sync.create_sample_databases()
    
    # Scanează intersecțiile
    print("\n2. Scanare intersecții...")
    intersections = sync.scan_intersections()
    
    # Detectează conflictele
    conflicts = sync.detect_conflicts(intersections)
    
    # Sincronizează (strategie: latest wins)
    print("\n3. Sincronizare...")
    stats = sync.sync_intersections(intersections, strategy="latest_wins")
    
    # Generează raportul
    sync.generate_sync_report(intersections, conflicts, stats)
    
    print("\n🎉 Sincronizarea bazelor de date a fost completată!")

if __name__ == "__main__":
    main()
