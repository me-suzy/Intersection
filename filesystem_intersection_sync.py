#!/usr/bin/env python3
"""
File System Intersection Sync
=============================
Sincronizează fișierele între două directoare diferite, găsind intersecțiile
și rezolvând inconsistențele între sistemele de fișiere.
"""

import os
import shutil
import hashlib
import json
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tempfile

@dataclass
class FileInfo:
    """Reprezintă informații despre un fișier"""
    path: str
    size: int
    modified_time: float
    checksum: str = ""
    is_directory: bool = False
    
    def __post_init__(self):
        if not self.checksum and not self.is_directory:
            self.checksum = self.calculate_checksum()
    
    def calculate_checksum(self) -> str:
        """Calculează checksum MD5 pentru fișier"""
        if self.is_directory:
            return ""
        
        try:
            with open(self.path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

class FileSystemIntersectionSync:
    """Sincronizează fișierele între două directoare"""
    
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.sync_log = []
        self.backup_dir = None
    
    def create_sample_directories(self):
        """Creează directoare de exemplu pentru testare"""
        print("📁 Creare directoare de exemplu...")
        
        # Creează directoare temporare
        self.source_dir = Path(tempfile.mkdtemp(prefix="source_"))
        self.target_dir = Path(tempfile.mkdtemp(prefix="target_"))
        
        # Structura sursă (aplicația veche)
        source_structure = {
            "app/": {
                "main.py": "# Aplicația principală - versiunea veche\ndef main():\n    print('Hello Old App')\n",
                "config/": {
                    "settings.json": '{"version": "1.0", "debug": true, "port": 8080}',
                    "database.py": "# Configurare bază de date\nDB_URL = 'sqlite:///old.db'"
                },
                "utils/": {
                    "helpers.py": "# Funcții utilitare\nimport os\ndef get_files():\n    return os.listdir('.')\n",
                    "validators.py": "# Validatori\nclass Validator:\n    pass\n"
                }
            },
            "docs/": {
                "README.md": "# Documentația veche\n\nAceasta este versiunea veche a aplicației.",
                "CHANGELOG.md": "# Changelog\n\n## v1.0\n- Prima versiune"
            },
            "tests/": {
                "test_main.py": "# Teste vechi\nimport unittest\nclass TestMain(unittest.TestCase):\n    pass\n"
            }
        }
        
        # Structura țintă (aplicația nouă)
        target_structure = {
            "src/": {
                "main.py": "# Aplicația principală - versiunea nouă\ndef main():\n    print('Hello New App')\n    print('New features added!')\n",
                "config/": {
                    "settings.json": '{"version": "2.0", "debug": false, "port": 9000, "new_feature": true}',
                    "database.py": "# Configurare bază de date nouă\nDB_URL = 'postgresql://new.db'"
                },
                "utils/": {
                    "helpers.py": "# Funcții utilitare îmbunătățite\nimport os\nfrom pathlib import Path\ndef get_files():\n    return list(Path('.').iterdir())\n",
                    "new_utils.py": "# Utilitare noi\nclass NewHelper:\n    def process(self):\n        return 'processed'\n"
                }
            },
            "docs/": {
                "README.md": "# Documentația nouă\n\nAceasta este versiunea nouă cu funcționalități îmbunătățite.",
                "API.md": "# API Documentation\n\nDocumentația pentru noua API."
            },
            "tests/": {
                "test_main.py": "# Teste noi\nimport unittest\nimport pytest\nclass TestMain(unittest.TestCase):\n    def test_new_feature(self):\n        pass\n"
            },
            "deploy/": {
                "Dockerfile": "# Docker pentru noua versiune\nFROM python:3.11\nCOPY . /app\nWORKDIR /app"
            }
        }
        
        # Creează structura sursă
        self._create_directory_structure(self.source_dir, source_structure)
        
        # Creează structura țintă
        self._create_directory_structure(self.target_dir, target_structure)
        
        print(f"   📂 Sursă: {self.source_dir}")
        print(f"   📂 Țintă: {self.target_dir}")
    
    def scan_intersections(self) -> Dict[str, List[FileInfo]]:
        """Scanează intersecțiile între cele două directoare"""
        print("\n🔍 Scanare intersecții între directoare...")
        
        source_files = self._scan_directory(self.source_dir)
        target_files = self._scan_directory(self.target_dir)
        
        # Normalizează căile pentru comparație
        source_paths = {self._normalize_path(f.path, self.source_dir) for f in source_files}
        target_paths = {self._normalize_path(f.path, self.target_dir) for f in target_files}
        
        intersection_paths = source_paths & target_paths
        only_source = source_paths - target_paths
        only_target = target_paths - source_paths
        
        print(f"   📊 Total fișiere în sursă: {len(source_files)}")
        print(f"   📊 Total fișiere în țintă: {len(target_files)}")
        print(f"   🔗 Intersecție (fișiere comune): {len(intersection_paths)}")
        print(f"   ➡️  Doar în sursă: {len(only_source)}")
        print(f"   ⬅️  Doar în țintă: {len(only_target)}")
        
        # Grupează fișierele
        intersection_files = []
        conflicts = []
        
        for path in intersection_paths:
            source_file = next(f for f in source_files if self._normalize_path(f.path, self.source_dir) == path)
            target_file = next(f for f in target_files if self._normalize_path(f.path, self.target_dir) == path)
            
            intersection_files.append((path, source_file, target_file))
            
            # Detectează conflicte
            if source_file.checksum != target_file.checksum:
                conflicts.append((path, source_file, target_file))
        
        return {
            "intersection_files": intersection_files,
            "conflicts": conflicts,
            "source_only": [f for f in source_files if self._normalize_path(f.path, self.source_dir) in only_source],
            "target_only": [f for f in target_files if self._normalize_path(f.path, self.target_dir) in only_target]
        }
    
    def detect_conflicts(self, intersections: Dict) -> List[Tuple]:
        """Detectează conflictele în intersecțiile găsite"""
        print("\n⚠️  Detectare conflicte în intersecții...")
        
        conflicts = intersections["conflicts"]
        
        for path, source_file, target_file in conflicts:
            print(f"   ⚠️  Conflict: {path}")
            print(f"      📏 Sursă: {source_file.size} bytes, {datetime.fromtimestamp(source_file.modified_time)}")
            print(f"      📏 Țintă: {target_file.size} bytes, {datetime.fromtimestamp(target_file.modified_time)}")
            print(f"      🔍 Checksum diferit: {source_file.checksum[:8]}... vs {target_file.checksum[:8]}...")
        
        print(f"   📋 Total conflicte: {len(conflicts)}")
        return conflicts
    
    def sync_intersections(self, intersections: Dict, strategy: str = "newer_wins") -> Dict[str, int]:
        """Sincronizează intersecțiile conform strategiei alese"""
        print(f"\n🔄 Sincronizare intersecții (strategie: {strategy})...")
        
        stats = {"updated": 0, "copied": 0, "errors": 0, "skipped": 0}
        
        # Creează backup
        self._create_backup()
        
        # 1. Rezolvă conflictele
        for path, source_file, target_file in intersections["conflicts"]:
            try:
                source_path = Path(self.source_dir) / path
                target_path = Path(self.target_dir) / path
                
                if strategy == "newer_wins":
                    if source_file.modified_time > target_file.modified_time:
                        shutil.copy2(source_path, target_path)
                        stats["updated"] += 1
                        self.sync_log.append(f"Updated {path} (source newer)")
                    else:
                        stats["skipped"] += 1
                        self.sync_log.append(f"Skipped {path} (target newer)")
                
                elif strategy == "source_wins":
                    shutil.copy2(source_path, target_path)
                    stats["updated"] += 1
                    self.sync_log.append(f"Updated {path} (source wins)")
                
                elif strategy == "target_wins":
                    stats["skipped"] += 1
                    self.sync_log.append(f"Skipped {path} (target wins)")
                
            except Exception as e:
                stats["errors"] += 1
                self.sync_log.append(f"Error syncing {path}: {e}")
        
        # 2. Copiază fișierele doar din sursă
        for file_info in intersections["source_only"]:
            try:
                relative_path = file_info.path.relative_to(self.source_dir)
                target_path = self.target_dir / relative_path
                
                # Creează directorul părinte dacă nu există
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(file_info.path, target_path)
                stats["copied"] += 1
                self.sync_log.append(f"Copied new file {relative_path}")
                
            except Exception as e:
                stats["errors"] += 1
                self.sync_log.append(f"Error copying {file_info.path}: {e}")
        
        return stats
    
    def generate_sync_report(self, intersections: Dict, stats: Dict):
        """Generează raportul de sincronizare"""
        print("\n" + "="*60)
        print("📋 RAPORT SINCRONIZARE FIȘIERE")
        print("="*60)
        
        print(f"📊 Statistici intersecții:")
        print(f"   • Total fișiere în sursă: {len(intersections['source_only']) + len(intersections['intersection_files'])}")
        print(f"   • Total fișiere în țintă: {len(intersections['target_only']) + len(intersections['intersection_files'])}")
        print(f"   • Intersecții găsite: {len(intersections['intersection_files'])}")
        print(f"   • Conflicte detectate: {len(intersections['conflicts'])}")
        
        print(f"\n🔄 Acțiuni efectuate:")
        print(f"   • Fișiere actualizate: {stats['updated']}")
        print(f"   • Fișiere copiate: {stats['copied']}")
        print(f"   • Fișiere sărite: {stats['skipped']}")
        print(f"   • Erori: {stats['errors']}")
        
        if self.sync_log:
            print(f"\n📝 Log detaliat:")
            for entry in self.sync_log[-10:]:
                print(f"   • {entry}")
        
        if self.backup_dir:
            print(f"\n💾 Backup creat la: {self.backup_dir}")
    
    def cleanup(self):
        """Șterge directoarele temporare"""
        import shutil
        if self.source_dir.exists():
            shutil.rmtree(self.source_dir)
        if self.target_dir.exists():
            shutil.rmtree(self.target_dir)
        if self.backup_dir and Path(self.backup_dir).exists():
            shutil.rmtree(self.backup_dir)
    
    def _create_directory_structure(self, base_path: Path, structure: Dict):
        """Creează structura de directoare și fișiere"""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # Este un director
                path.mkdir(parents=True, exist_ok=True)
                self._create_directory_structure(path, content)
            else:
                # Este un fișier
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
    
    def _scan_directory(self, directory: Path) -> List[FileInfo]:
        """Scanează un director și returnează informații despre fișiere"""
        files = []
        
        for root, dirs, filenames in os.walk(directory):
            root_path = Path(root)
            
            for filename in filenames:
                file_path = root_path / filename
                try:
                    stat = file_path.stat()
                    file_info = FileInfo(
                        path=str(file_path),
                        size=stat.st_size,
                        modified_time=stat.st_mtime
                    )
                    files.append(file_info)
                except Exception:
                    continue
        
        return files
    
    def _normalize_path(self, file_path: str, base_dir: Path) -> str:
        """Normalizează calea relativă pentru comparație"""
        path = Path(file_path)
        try:
            return str(path.relative_to(base_dir)).replace('\\', '/')
        except ValueError:
            return str(path).replace('\\', '/')
    
    def _create_backup(self):
        """Creează backup pentru directoarele țintă"""
        self.backup_dir = Path(tempfile.mkdtemp(prefix="backup_"))
        shutil.copytree(self.target_dir, self.backup_dir / "target_backup")

def main():
    """Funcția principală pentru testarea sincronizării"""
    print("📁 FILESYSTEM INTERSECTION SYNC")
    print("="*50)
    
    # Inițializează sincronizatorul
    sync = FileSystemIntersectionSync("source", "target")
    
    try:
        # Creează directoarele de exemplu
        print("1. Creare directoare de exemplu...")
        sync.create_sample_directories()
        
        # Scanează intersecțiile
        print("\n2. Scanare intersecții...")
        intersections = sync.scan_intersections()
        
        # Detectează conflictele
        conflicts = sync.detect_conflicts(intersections)
        
        # Sincronizează (strategie: newer wins)
        print("\n3. Sincronizare...")
        stats = sync.sync_intersections(intersections, strategy="newer_wins")
        
        # Generează raportul
        sync.generate_sync_report(intersections, stats)
        
        print("\n🎉 Sincronizarea fișierelor a fost completată!")
        
    finally:
        # Curăță directoarele temporare
        input("\nApasă Enter pentru a șterge directoarele temporare...")
        sync.cleanup()

if __name__ == "__main__":
    main()
