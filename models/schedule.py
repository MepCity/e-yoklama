from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Pazartesi ... 6=Pazar
    start_time = Column(String(5), nullable=False)  # "HH:MM"
    end_time = Column(String(5), nullable=False)     # "HH:MM"
    room = Column(String(50), nullable=True)

    # Geofence (sinif konumu — NFR-05/06)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    radius_m = Column(Integer, default=100)

    # Relationship
    course = relationship('Course', back_populates='schedules')
