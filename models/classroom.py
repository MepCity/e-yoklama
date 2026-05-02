from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from database import Base
from utils.helpers import utcnow_str


class Building(Base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_code = Column(String(10), unique=True, nullable=False)  # T1, T2, T3, T4, T5
    building_name = Column(String(100), nullable=False)  # Teknik Bilimler Fakültesi, Mühendislik Fakültesi
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String(50), nullable=False, default=utcnow_str)

    def __repr__(self):
        return f'<Building {self.building_code}: {self.building_name}>'


class Classroom(Base):
    __tablename__ = 'classrooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, nullable=False)  # Foreign key Building
    classroom_code = Column(String(10), nullable=False)  # Z01-Z09, 101-109
    classroom_name = Column(String(100), nullable=False)  # Z01 Laboratuvar, 101 Derslik
    capacity = Column(Integer, nullable=True)  # Kapasite
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String(50), nullable=False, default=utcnow_str)

    __table_args__ = (
        UniqueConstraint('building_id', 'classroom_code', name='uq_building_classroom'),
    )

    def __repr__(self):
        return f'<Classroom {self.classroom_code}: {self.classroom_name}>'
