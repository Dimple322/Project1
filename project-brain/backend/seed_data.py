#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Seed database with demo data - Oil & Gas Project"""

import os
os.environ.setdefault("DATABASE_URL", "postgresql://brain_user:brain_password@postgres:5432/project_brain")

from db import SessionLocal
from models import (
    Project, Phase, Facility, Well, Subsystem, Person, 
    Contractor, Lexicon, Document, RegistryEntity, RegistryRelation,
    Lexicon as LexiconModel
)
from datetime import datetime
import uuid


def seed_registry(db, project_key="norflex_project"):
    """Seed the registry with oil & gas entities"""
    
    print("Seeding registry entities...")
    
    # Phases (6 project phases)
    phases_data = [
        {"name": "Exploration", "type": "phase"},
        {"name": "Development", "type": "phase"},
        {"name": "Production", "type": "phase"},
        {"name": "Operations", "type": "phase"},
        {"name": "Decommissioning", "type": "phase"},
        {"name": "Remediation", "type": "phase"},
    ]
    
    phase_entities = {}
    for phase_data in phases_data:
        entity = RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=phase_data["name"].lower().replace(" ", "_"),
            type=phase_data["type"],
            canonical_name=phase_data["name"],
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        db.flush()
        phase_entities[phase_data["name"]] = entity.id
    
    # Facilities (2)
    facilities_data = [
        {
            "name": "Norflex A",
            "aliases": ["NFA", "Platform-A", "Facility-A"],
            "type": "facility"
        },
        {
            "name": "Norflex B",
            "aliases": ["NFB", "Platform-B", "Facility-B"],
            "type": "facility"
        }
    ]
    
    facility_entities = {}
    for fac_data in facilities_data:
        entity = RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=fac_data["name"].lower().replace(" ", "_"),
            type=fac_data["type"],
            canonical_name=fac_data["name"],
            aliases=fac_data.get("aliases", []),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        db.flush()
        facility_entities[fac_data["name"]] = entity.id
    
    # Subsystems (4 under facilities)
    subsystems_data = [
        {"name": "Production Separator", "facility": "Norflex A", "aliases": ["PS", "SEP"]},
        {"name": "Water Injection System", "facility": "Norflex A", "aliases": ["WIS", "INJSYS"]},
        {"name": "Compression Unit", "facility": "Norflex B", "aliases": ["CU", "COMPUNIT"]},
        {"name": "Metering Skid", "facility": "Norflex B", "aliases": ["MS", "METER"]},
    ]
    
    subsystem_entities = {}
    for sub_data in subsystems_data:
        parent_id = facility_entities.get(sub_data["facility"])
        entity = RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=sub_data["name"].lower().replace(" ", "_"),
            type="subsystem",
            canonical_name=sub_data["name"],
            aliases=sub_data.get("aliases", []),
            parent_id=parent_id,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        db.flush()
        subsystem_entities[sub_data["name"]] = entity.id
        
        # Add PART_OF relation
        if parent_id:
            rel = RegistryRelation(
                id=str(uuid.uuid4()),
                project_key=project_key,
                from_entity_id=entity.id,
                to_entity_id=parent_id,
                relation_type="PART_OF",
                confidence=1.0,
                source="manual",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(rel)
    
    # Wells (6)
    wells_data = [
        {"name": "Well-01", "facility": "Norflex A", "aliases": ["W01", "WELL01"]},
        {"name": "Well-02", "facility": "Norflex A", "aliases": ["W02", "WELL02"]},
        {"name": "Well-03", "facility": "Norflex A", "aliases": ["W03", "WELL03"]},
        {"name": "Well-04", "facility": "Norflex B", "aliases": ["W04", "WELL04"]},
        {"name": "Well-05", "facility": "Norflex B", "aliases": ["W05", "WELL05"]},
        {"name": "Well-06", "facility": "Norflex B", "aliases": ["W06", "WELL06"]},
    ]
    
    well_entities = {}
    for well_data in wells_data:
        parent_id = facility_entities.get(well_data["facility"])
        entity = RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=well_data["name"].lower(),
            type="well",
            canonical_name=well_data["name"],
            aliases=well_data.get("aliases", []),
            parent_id=parent_id,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        db.flush()
        well_entities[well_data["name"]] = entity.id
        
        # Add PART_OF relation
        if parent_id:
            rel = RegistryRelation(
                id=str(uuid.uuid4()),
                project_key=project_key,
                from_entity_id=entity.id,
                to_entity_id=parent_id,
                relation_type="PART_OF",
                confidence=1.0,
                source="manual",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(rel)
    
    # Contractors (2)
    contractors_data = [
        {"name": "PetroTech Services", "aliases": ["PTS", "PETROTECH"]},
        {"name": "Offshore Engineering Inc", "aliases": ["OEI", "OFFSHORE-ENG"]},
    ]
    
    contractor_entities = {}
    for cont_data in contractors_data:
        entity = RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=cont_data["name"].lower().replace(" ", "_"),
            type="contractor",
            canonical_name=cont_data["name"],
            aliases=cont_data.get("aliases", []),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        db.flush()
        contractor_entities[cont_data["name"]] = entity.id
    
    # People (5)
    people_data = [
        {"name": "John Smith", "role": "Project Manager"},
        {"name": "Maria Garcia", "role": "Engineering Lead"},
        {"name": "Ahmed Hassan", "role": "Operations Supervisor"},
        {"name": "Elena Volkova", "role": "Quality Assurance"},
        {"name": "David Chen", "role": "Safety Officer"},
    ]
    
    person_entities = {}
    for person_data in people_data:
        entity = RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=person_data["name"].lower().replace(" ", "_"),
            type="person",
            canonical_name=person_data["name"],
            attributes={"role": person_data["role"]},
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(entity)
        db.flush()
        person_entities[person_data["name"]] = entity.id
    
    db.commit()
    print(f"? Seeded {len(phases_data)} phases, {len(facilities_data)} facilities, {len(subsystems_data)} subsystems, {len(wells_data)} wells, {len(contractors_data)} contractors, {len(people_data)} people")
    
    return {
        "phases": phase_entities,
        "facilities": facility_entities,
        "subsystems": subsystem_entities,
        "wells": well_entities,
        "contractors": contractor_entities,
        "people": person_entities
    }


def seed_lexicon(db):
    """Seed oil & gas lexicon"""
    
    print("Seeding lexicon...")
    
    lexicon_data = [
        # Abbreviations
        {"term": "КИП", "canonical": "контрольно-измерительные приборы", "category": "abbreviation"},
        {"term": "УКПГ", "canonical": "установка комплексной подготовки газа", "category": "abbreviation"},
        {"term": "ДКС", "canonical": "дожимная компрессорная станция", "category": "abbreviation"},
        {"term": "ППД", "canonical": "поддержание пластового давления", "category": "abbreviation"},
        {"term": "ГТИ", "canonical": "геолого-техническое совещание", "category": "abbreviation"},
        {"term": "ПНР", "canonical": "подземное хранилище природного газа", "category": "abbreviation"},
        {"term": "БИН", "canonical": "база информационного насоса", "category": "abbreviation"},
        {"term": "НКТ", "canonical": "насосно-компрессорные трубы", "category": "abbreviation"},
        
        # Synonyms
        {"term": "скважина", "canonical": "well", "category": "synonym"},
        {"term": "скв", "canonical": "well", "category": "abbreviation"},
        {"term": "добыча", "canonical": "production", "category": "synonym"},
        {"term": "платформа", "canonical": "facility", "category": "synonym"},
        {"term": "объект", "canonical": "asset", "category": "synonym"},
    ]
    
    for lex_data in lexicon_data:
        existing = db.query(LexiconModel).filter_by(term=lex_data["term"]).first()
        if not existing:
            lex = LexiconModel(
                id=str(uuid.uuid4()),
                term=lex_data["term"],
                canonical_form=lex_data["canonical"],
                category=lex_data["category"],
                confidence=0.95,
                source="manual",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(lex)
    
    db.commit()
    print(f"? Seeded {len(lexicon_data)} lexicon terms")


def seed_database():
    db = SessionLocal()
    
    try:
        # Seed registry
        seed_registry(db, project_key="norflex_project")
        
        # Seed lexicon
        seed_lexicon(db)
        
        print("\n? Database seeding completed successfully!")
        
    except Exception as e:
        print(f"? Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
        db.flush()
        
        # Create wells
        well1 = Well(
            id=str(uuid.uuid4()),
            facility_id=facility.id,
            name="Well A-01",
            canonical_name="well_a_01",
            description="Production well A-01",
            aliases=["A01"]
        )
        db.add(well1)
        db.flush()
        
        well2 = Well(
            id=str(uuid.uuid4()),
            facility_id=facility.id,
            name="Well A-02",
            canonical_name="well_a_02",
            description="Production well A-02"
        )
        db.add(well2)
        db.flush()
        
        # Create subsystems
        subsystem_pump = Subsystem(
            id=str(uuid.uuid4()),
            facility_id=facility.id,
            name="Pump System",
            canonical_name="pump_system",
            description="Main production pump system",
            aliases=["PS", "Main Pump"]
        )
        db.add(subsystem_pump)
        db.flush()
        
        subsystem_separator = Subsystem(
            id=str(uuid.uuid4()),
            facility_id=facility.id,
            name="Separator System",
            canonical_name="separator_system",
            description="Oil/water separator system",
            aliases=["SEP", "3-Phase Sep"]
        )
        db.add(subsystem_separator)
        db.flush()
        
        # Create persons
        person_engineer = Person(
            id=str(uuid.uuid4()),
            name="John Smith",
            canonical_name="john_smith",
            role="Lead Engineer",
            aliases=["J. Smith", "JS"]
        )
        db.add(person_engineer)
        db.flush()
        
        person_manager = Person(
            id=str(uuid.uuid4()),
            name="Jane Doe",
            canonical_name="jane_doe",
            role="Project Manager",
            aliases=["J. Doe", "JD"]
        )
        db.add(person_manager)
        db.flush()
        
        # Create contractor
        contractor = Contractor(
            id=str(uuid.uuid4()),
            name="TechCorp Solutions",
            canonical_name="techcorp_solutions",
            aliases=["TCS", "TechCorp"]
        )
        db.add(contractor)
        db.flush()
        
        # Create lexicon entries
        lexicon_entries = [
            Lexicon(
                id=str(uuid.uuid4()),
                term="BOP",
                canonical_form="Blowout Preventer",
                category="abbreviation",
                aliases=["B.O.P"],
                source="manual",
                confidence=1.0
            ),
            Lexicon(
                id=str(uuid.uuid4()),
                term="ESP",
                canonical_form="Electrical Submersible Pump",
                category="abbreviation",
                aliases=["E.S.P"],
                source="manual",
                confidence=1.0
            ),
            Lexicon(
                id=str(uuid.uuid4()),
                term="3-Phase Sep",
                canonical_form="Three-Phase Separator",
                category="synonym",
                aliases=["3PS", "3 Phase Separator"],
                source="manual",
                confidence=0.95
            ),
            Lexicon(
                id=str(uuid.uuid4()),
                term="SCADA",
                canonical_form="Supervisory Control and Data Acquisition",
                category="abbreviation",
                aliases=["S.C.A.D.A"],
                source="manual",
                confidence=1.0
            ),
            Lexicon(
                id=str(uuid.uuid4()),
                term="ROV",
                canonical_form="Remotely Operated Vehicle",
                category="abbreviation",
                aliases=["R.O.V"],
                source="manual",
                confidence=1.0
            ),
        ]
        
        for entry in lexicon_entries:
            db.add(entry)
        
        db.commit()
        
        print("? Database seeded successfully!")
        print(f"  - Project: {project.name}")
        print(f"  - Facility: {facility.name}")
        print(f"  - Wells: {well1.name}, {well2.name}")
        print(f"  - Subsystems: {subsystem_pump.name}, {subsystem_separator.name}")
        print(f"  - Persons: {person_engineer.name}, {person_manager.name}")
        print(f"  - Contractor: {contractor.name}")
        print(f"  - Lexicon entries: {len(lexicon_entries)}")
        
    except Exception as e:
        db.rollback()
        print(f"? Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
