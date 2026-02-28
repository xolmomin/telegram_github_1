from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Model


class Region(Model):
    name: Mapped[str] = mapped_column(String(255))
    districts: Mapped[list['District']] = relationship('District', back_populates='region')


class District(Model):
    name: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int] = mapped_column(ForeignKey('regions.id'))
    region: Mapped['Region'] = relationship('Region', back_populates='districts')

    def __str__(self):
        return f"{self.id} - {self.name}"

    def __repr__(self):
        return self.name
