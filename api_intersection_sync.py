#!/usr/bin/env python3
"""
API Intersection Sync
=====================
Sincronizează datele între două API-uri diferite, găsind intersecțiile
și rezolvând inconsistențele între servicii.
"""

import requests
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import time
from urllib.parse import urljoin

@dataclass
class APIEndpoint:
    """Reprezintă un endpoint API"""
    url: str
    method: str
    headers: Dict[str, str]
    timeout: int = 30
    
@dataclass
class APIRecord:
    """Reprezintă o înregistrare din API"""
    id: str
    data: Dict[str, Any]
    last_modified: str
    checksum: str = ""
    source_api: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self.calculate_checksum()
    
    def calculate_checksum(self) -> str:
        """Calculează checksum pentru detectarea modificărilor"""
        data_str = json.dumps(self.data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(data_str.encode()).hexdigest()

class MockAPIServer:
    """Server API simulat pentru testare"""
    
    def __init__(self, port: int):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.data = {}
        self.requests_log = []
    
    def start_server(self):
        """Pornește serverul mock"""
        print(f"🚀 Pornire server mock pe port {self.port}")
        
        # Date de exemplu pentru serverul 1 (sistem vechi)
        if self.port == 8001:
            self.data = {
                "users": [
                    {
                        "id": "1",
                        "name": "Ion Popescu",
                        "email": "ion@email.com",
                        "phone": "0712345678",
                        "status": "active",
                        "last_login": "2023-01-15T10:30:00Z",
                        "permissions": ["read", "write"]
                    },
                    {
                        "id": "2", 
                        "name": "Maria Ionescu",
                        "email": "maria@gmail.com",
                        "phone": "0798765432",
                        "status": "inactive",
                        "last_login": "2023-02-20T14:15:00Z",
                        "permissions": ["read"]
                    },
                    {
                        "id": "3",
                        "name": "Andrei Dumitrescu", 
                        "email": "andrei@yahoo.com",
                        "phone": "0723456789",
                        "status": "active",
                        "last_login": "2023-03-10T09:45:00Z",
                        "permissions": ["read", "write", "admin"]
                    }
                ],
                "orders": [
                    {
                        "id": "ORD-001",
                        "user_id": "1",
                        "amount": 150.50,
                        "status": "completed",
                        "created_at": "2023-01-10T08:00:00Z"
                    },
                    {
                        "id": "ORD-002", 
                        "user_id": "2",
                        "amount": 75.25,
                        "status": "pending",
                        "created_at": "2023-02-15T12:30:00Z"
                    }
                ]
            }
        
        # Date de exemplu pentru serverul 2 (sistem nou)
        elif self.port == 8002:
            self.data = {
                "users": [
                    {
                        "id": "1",
                        "name": "Ion Popescu",
                        "email": "ion.popescu@company.com",  # Email modificat
                        "phone": "0712345678",
                        "status": "active",
                        "last_login": "2023-12-01T16:20:00Z",  # Login mai recent
                        "permissions": ["read", "write", "delete"],  # Permisiuni noi
                        "department": "IT"  # Câmp nou
                    },
                    {
                        "id": "2",
                        "name": "Maria Ionescu", 
                        "email": "maria@gmail.com",
                        "phone": "0798765432",
                        "status": "active",  # Status modificat
                        "last_login": "2023-02-20T14:15:00Z",
                        "permissions": ["read", "write"],  # Permisiuni noi
                        "department": "HR"  # Câmp nou
                    },
                    {
                        "id": "4",  # ID nou
                        "name": "Elena Vasilescu",
                        "email": "elena@company.com",
                        "phone": "0734567890",
                        "status": "active",
                        "last_login": "2023-12-01T11:00:00Z",
                        "permissions": ["read"],
                        "department": "Finance"
                    }
                ],
                "orders": [
                    {
                        "id": "ORD-001",
                        "user_id": "1",
                        "amount": 150.50,
                        "status": "completed",
                        "created_at": "2023-01-10T08:00:00Z",
                        "payment_method": "credit_card",  # Câmp nou
                        "shipping_address": "București, România"  # Câmp nou
                    },
                    {
                        "id": "ORD-003",  # ID nou
                        "user_id": "4",
                        "amount": 200.00,
                        "status": "processing",
                        "created_at": "2023-12-01T10:00:00Z",
                        "payment_method": "bank_transfer",
                        "shipping_address": "Cluj-Napoca, România"
                    }
                ]
            }
    
    def get_endpoint(self, path: str) -> str:
        """Returnează URL-ul complet pentru un endpoint"""
        return urljoin(self.base_url, path)

class APIIntersectionSync:
    """Sincronizează datele între două API-uri"""
    
    def __init__(self, api1: MockAPIServer, api2: MockAPIServer):
        self.api1 = api1
        self.api2 = api2
        self.sync_log = []
    
    def scan_intersections(self) -> Dict[str, Any]:
        """Scanează intersecțiile între cele două API-uri"""
        print("\n🔍 Scanare intersecții între API-uri...")
        
        # Simulează cererile către API-uri
        api1_data = self._fetch_api_data(self.api1, "API-1")
        api2_data = self._fetch_api_data(self.api2, "API-2")
        
        intersections = {}
        
        # Pentru fiecare tip de resursă (users, orders, etc.)
        for resource_type in ["users", "orders"]:
            if resource_type in api1_data and resource_type in api2_data:
                api1_records = {record["id"]: APIRecord(
                    id=record["id"],
                    data=record,
                    last_modified=record.get("last_login", record.get("created_at", "")),
                    source_api="API-1"
                ) for record in api1_data[resource_type]}
                
                api2_records = {record["id"]: APIRecord(
                    id=record["id"],
                    data=record,
                    last_modified=record.get("last_login", record.get("created_at", "")),
                    source_api="API-2"
                ) for record in api2_data[resource_type]}
                
                # Găsește intersecțiile
                common_ids = set(api1_records.keys()) & set(api2_records.keys())
                only_api1 = set(api1_records.keys()) - set(api2_records.keys())
                only_api2 = set(api2_records.keys()) - set(api1_records.keys())
                
                intersections[resource_type] = {
                    "common_records": common_ids,
                    "api1_only": only_api1,
                    "api2_only": only_api2,
                    "api1_data": api1_records,
                    "api2_data": api2_records
                }
                
                print(f"   📊 {resource_type}:")
                print(f"      🔗 Intersecție: {len(common_ids)}")
                print(f"      ➡️  Doar în API-1: {len(only_api1)}")
                print(f"      ⬅️  Doar în API-2: {len(only_api2)}")
        
        return intersections
    
    def detect_conflicts(self, intersections: Dict) -> Dict[str, List[Tuple]]:
        """Detectează conflictele în intersecțiile găsite"""
        print("\n⚠️  Detectare conflicte în intersecții...")
        
        conflicts = {}
        
        for resource_type, data in intersections.items():
            conflicts[resource_type] = []
            
            for record_id in data["common_records"]:
                api1_record = data["api1_data"][record_id]
                api2_record = data["api2_data"][record_id]
                
                if api1_record.checksum != api2_record.checksum:
                    conflict = (record_id, api1_record, api2_record)
                    conflicts[resource_type].append(conflict)
                    
                    print(f"   ⚠️  Conflict {resource_type} ID {record_id}:")
                    
                    # Identifică câmpurile diferite
                    different_fields = self._get_different_fields(api1_record.data, api2_record.data)
                    for field in different_fields:
                        api1_value = api1_record.data.get(field, "N/A")
                        api2_value = api2_record.data.get(field, "N/A")
                        print(f"      {field}: '{api1_value}' vs '{api2_value}'")
        
        total_conflicts = sum(len(conflicts) for conflicts in conflicts.values())
        print(f"   📋 Total conflicte: {total_conflicts}")
        
        return conflicts
    
    def sync_intersections(self, intersections: Dict, conflicts: Dict, strategy: str = "latest_wins") -> Dict[str, int]:
        """Sincronizează intersecțiile conform strategiei alese"""
        print(f"\n🔄 Sincronizare intersecții (strategie: {strategy})...")
        
        stats = {"updated": 0, "created": 0, "errors": 0, "skipped": 0}
        
        for resource_type, data in intersections.items():
            print(f"\n   📋 Procesare {resource_type}...")
            
            # 1. Rezolvă conflictele
            for record_id, api1_record, api2_record in conflicts.get(resource_type, []):
                try:
                    if strategy == "latest_wins":
                        # Compară timestamp-urile
                        if self._parse_timestamp(api1_record.last_modified) > self._parse_timestamp(api2_record.last_modified):
                            self._update_api_record(self.api2, resource_type, api1_record)
                            stats["updated"] += 1
                            self.sync_log.append(f"Updated {resource_type}/{record_id} (API-1 newer)")
                        else:
                            stats["skipped"] += 1
                            self.sync_log.append(f"Skipped {resource_type}/{record_id} (API-2 newer)")
                    
                    elif strategy == "api1_wins":
                        self._update_api_record(self.api2, resource_type, api1_record)
                        stats["updated"] += 1
                        self.sync_log.append(f"Updated {resource_type}/{record_id} (API-1 wins)")
                    
                    elif strategy == "api2_wins":
                        self._update_api_record(self.api1, resource_type, api2_record)
                        stats["updated"] += 1
                        self.sync_log.append(f"Updated {resource_type}/{record_id} (API-2 wins)")
                    
                except Exception as e:
                    stats["errors"] += 1
                    self.sync_log.append(f"Error syncing {resource_type}/{record_id}: {e}")
            
            # 2. Creează înregistrările doar din API-1 în API-2
            for record_id in data["api1_only"]:
                try:
                    api1_record = data["api1_data"][record_id]
                    self._update_api_record(self.api2, resource_type, api1_record)
                    stats["created"] += 1
                    self.sync_log.append(f"Created {resource_type}/{record_id} in API-2")
                except Exception as e:
                    stats["errors"] += 1
                    self.sync_log.append(f"Error creating {resource_type}/{record_id}: {e}")
            
            # 3. Creează înregistrările doar din API-2 în API-1
            for record_id in data["api2_only"]:
                try:
                    api2_record = data["api2_data"][record_id]
                    self._update_api_record(self.api1, resource_type, api2_record)
                    stats["created"] += 1
                    self.sync_log.append(f"Created {resource_type}/{record_id} in API-1")
                except Exception as e:
                    stats["errors"] += 1
                    self.sync_log.append(f"Error creating {resource_type}/{record_id}: {e}")
        
        return stats
    
    def generate_sync_report(self, intersections: Dict, conflicts: Dict, stats: Dict):
        """Generează raportul de sincronizare"""
        print("\n" + "="*60)
        print("📋 RAPORT SINCRONIZARE API-URI")
        print("="*60)
        
        total_conflicts = sum(len(conflicts) for conflicts in conflicts.values())
        total_intersections = sum(len(data["common_records"]) for data in intersections.values())
        
        print(f"📊 Statistici intersecții:")
        print(f"   • Total intersecții: {total_intersections}")
        print(f"   • Total conflicte: {total_conflicts}")
        
        for resource_type, data in intersections.items():
            print(f"   • {resource_type}: {len(data['common_records'])} comune, {len(conflicts.get(resource_type, []))} conflicte")
        
        print(f"\n🔄 Acțiuni efectuate:")
        print(f"   • Înregistrări actualizate: {stats['updated']}")
        print(f"   • Înregistrări create: {stats['created']}")
        print(f"   • Înregistrări sărite: {stats['skipped']}")
        print(f"   • Erori: {stats['errors']}")
        
        if self.sync_log:
            print(f"\n📝 Log detaliat:")
            for entry in self.sync_log[-10:]:
                print(f"   • {entry}")
    
    def _fetch_api_data(self, api: MockAPIServer, api_name: str) -> Dict:
        """Simulează fetch-ul datelor de la API"""
        print(f"   📡 Fetching data from {api_name}...")
        time.sleep(0.1)  # Simulează latența
        return api.data.copy()
    
    def _get_different_fields(self, data1: Dict, data2: Dict) -> List[str]:
        """Identifică câmpurile care sunt diferite între două înregistrări"""
        all_keys = set(data1.keys()) | set(data2.keys())
        different = []
        
        for key in all_keys:
            value1 = data1.get(key)
            value2 = data2.get(key)
            if value1 != value2:
                different.append(key)
        
        return different
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parsează un timestamp string și returnează timestamp-ul Unix"""
        try:
            # Format simplu pentru demonstrație
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except:
            return 0.0
    
    def _update_api_record(self, target_api: MockAPIServer, resource_type: str, record: APIRecord):
        """Actualizează o înregistrare în API-ul țintă"""
        if record.id not in target_api.data[resource_type]:
            # Creează o nouă înregistrare
            target_api.data[resource_type].append(record.data)
        else:
            # Actualizează înregistrarea existentă
            for i, existing_record in enumerate(target_api.data[resource_type]):
                if existing_record["id"] == record.id:
                    target_api.data[resource_type][i] = record.data
                    break

def main():
    """Funcția principală pentru testarea sincronizării"""
    print("🌐 API INTERSECTION SYNC")
    print("="*50)
    
    # Inițializează serverele mock
    api1 = MockAPIServer(8001)
    api2 = MockAPIServer(8002)
    
    # Pornește serverele
    print("1. Pornire servere mock...")
    api1.start_server()
    api2.start_server()
    
    # Inițializează sincronizatorul
    sync = APIIntersectionSync(api1, api2)
    
    # Scanează intersecțiile
    print("\n2. Scanare intersecții...")
    intersections = sync.scan_intersections()
    
    # Detectează conflictele
    conflicts = sync.detect_conflicts(intersections)
    
    # Sincronizează (strategie: latest wins)
    print("\n3. Sincronizare...")
    stats = sync.sync_intersections(intersections, conflicts, strategy="latest_wins")
    
    # Generează raportul
    sync.generate_sync_report(intersections, conflicts, stats)
    
    print("\n🎉 Sincronizarea API-urilor a fost completată!")
    print("\n📊 Date finale în API-1:")
    for resource_type, records in api1.data.items():
        print(f"   {resource_type}: {len(records)} înregistrări")
    
    print("\n📊 Date finale în API-2:")
    for resource_type, records in api2.data.items():
        print(f"   {resource_type}: {len(records)} înregistrări")

if __name__ == "__main__":
    main()
