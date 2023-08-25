from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import VARCHAR, Integer, Date, Text, Boolean, Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum


role_enum = ENUM('admin', 'inspector', 'client', name='role_enum')
role_python_enum = Enum('role_python_enum', ['admin', 'inspector', 'client'])

method_enum = ENUM('ВИК', 'УЗТ', 'УК', 'МК', 'ПВК', 'ГИ', name='method_enum')
method_python_enum = Enum('method_python_enum', ['ВИК', 'УЗТ', 'УК', 'МК', 'ПВК', 'ГИ'])

class Base(DeclarativeBase):
    pass

class Img(Base):
    __tablename__ = 'images'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    src: Mapped[VARCHAR] = mapped_column(VARCHAR(100))
    
class Company(Base):
    __tablename__ = 'companies'
    
    id = mapped_column(Integer, primary_key=True, nullable=False)
    name = mapped_column(VARCHAR(100))
    logo_id = mapped_column(Integer, ForeignKey('images.id'))
    units: Mapped[List["Unit"]] = relationship("Unit", back_populates="company")
    
class Unit(Base):
    __tablename__ = 'units'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey('companies.id'))
    supervisor_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    location: Mapped[VARCHAR] = mapped_column(VARCHAR(50))
    sector: Mapped[VARCHAR] = mapped_column(VARCHAR(50)) # Участок
    setup_name: Mapped[VARCHAR] = mapped_column(VARCHAR(50)) # Номер установки
    
    company: Mapped[Company] = relationship("Company", back_populates="units")
    supervisor: Mapped["User"] = relationship("User", back_populates="units")
    hardwares: Mapped[List["Hardware"]] = relationship("Hardware", back_populates="unit")
    
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    password: Mapped[str] = mapped_column(VARCHAR(100))
    name: Mapped[str] = mapped_column(VARCHAR(150))
    role: Mapped[ENUM] = mapped_column(role_enum)
    phone_number: Mapped[str] = mapped_column(VARCHAR(12))
    email: Mapped[str] = mapped_column(VARCHAR(255))
    
    birthdate = mapped_column(Date)
    position = mapped_column(VARCHAR(255))
    certificate_number = mapped_column(VARCHAR(255))
    certificated_till = mapped_column(Date)
    
    units: Mapped[List['Unit']] = relationship('Unit', back_populates='supervisor') 
    reports: Mapped[List['Report']] = relationship('Report', back_populates='inspector') 
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, role={self.role!r})"
        

class Tool(Base):
    __tablename__ = 'tools'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  = mapped_column(VARCHAR(255))
    method: Mapped[ENUM] = mapped_column(method_enum)
    model: Mapped[str]  = mapped_column(VARCHAR(255))
    factory_number: Mapped[str]  = mapped_column(VARCHAR(255))
    inventory_number: Mapped[str]  = mapped_column(VARCHAR(255))
    checkup_certificate_number: Mapped[str]  = mapped_column(VARCHAR(255))
    prev_checkup: Mapped[Date] = mapped_column(Date, nullable=True)
    next_checkup: Mapped[Date] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)

class Catalogue(Base):
    __tablename__ = 'catalogue'
    
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(VARCHAR(200))
    comment = mapped_column(VARCHAR(300))
    
    manufacturer = mapped_column(VARCHAR(200))
    batch_number = mapped_column(VARCHAR(200))
    
    # In years
    life_time = mapped_column(Integer)
    
    temp_min = mapped_column(Integer)
    temp_max = mapped_column(Integer)
    
    T1 = mapped_column(Float)
    T2 = mapped_column(Float)
    T3 = mapped_column(Float)
    T4 = mapped_column(Float)
    T5 = mapped_column(Float)
    T6 = mapped_column(Float)
    T7 = mapped_column(Float)
    
    pressure_max = mapped_column(Float)
    
    # Max pressure on the first stage, MPa 
    stage1 = mapped_column(Float)
    # Duration of the first stage, min
    duration1 = mapped_column(Integer)
    
    stage2 = mapped_column(Float)
    duration2 = mapped_column(Integer)
    
    stage3 = mapped_column(Float)
    duration3 = mapped_column(Integer)
    
    stage4 = mapped_column(Float)
    duration4 = mapped_column(Integer)
    
    hardwares: Mapped[List["Hardware"]] = relationship('Hardware', back_populates='type')

class Hardware(Base):
    __tablename__ = 'hardware'
    
    id = mapped_column(Integer, primary_key=True)
    company_id = mapped_column(Integer, ForeignKey('companies.id'))
    unit_id = mapped_column(Integer, ForeignKey('units.id'))
    catalogue_id = mapped_column(Integer, ForeignKey('catalogue.id'))
    tape_number = mapped_column(Text)
    
    serial_number = mapped_column(Text)
    # When it started to be used
    commissioned = mapped_column(Date)
    
    last_checkup = mapped_column(Date)
    next_checkup = mapped_column(Date)
    
    type: Mapped[Catalogue] = relationship("Catalogue", back_populates="hardwares")
    unit: Mapped[Unit] = relationship("Unit", back_populates="hardwares")
    reports: Mapped[List["Report"]] = relationship('Report', back_populates='hardware')

class Report(Base):
    __tablename__ = 'reports'
    
    id = mapped_column(Integer, primary_key=True)
    hardware_id = mapped_column(Integer, ForeignKey('hardware.id'))
    inspector_id = mapped_column(Integer, ForeignKey('users.id'))
    checkup = mapped_column(Date)
    
    ambinet_temp = mapped_column(Float)
    total_light = mapped_column(Float)
    surface_light = mapped_column(Float)
    
    visual_good = mapped_column(Boolean)
    visual_comment = mapped_column(Text)
    
    T1 = mapped_column(Float)
    T2 = mapped_column(Float)
    T3 = mapped_column(Float)
    T4 = mapped_column(Float)
    T5 = mapped_column(Float)
    T6 = mapped_column(Float)
    T7 = mapped_column(Float)
    
    uzt_result = mapped_column(Boolean)
    residual = mapped_column(Float)
    
    UK_good = mapped_column(Boolean)
    UK_comment = mapped_column(Text)
    
    MK_good = mapped_column(Boolean)
    MK_comment = mapped_column(Text)
    
    hydro_result = mapped_column(Text)
    GI_preventor_good = mapped_column(Boolean)
    
    hardware: Mapped[Hardware] = relationship('Hardware', back_populates='reports')
    inspector: Mapped[User] = relationship('User', back_populates='reports') 