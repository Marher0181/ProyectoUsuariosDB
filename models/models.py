from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Producto(db.Model):
    __tablename__ = 'productos'
    idProducto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    idUsuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    idRol = db.Column(db.Integer, db.ForeignKey('roles.idRol'), nullable=True)
    rol = db.relationship('Rol', backref='usuarios')

class Rol(db.Model):
    __tablename__ = 'roles'
    idRol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

class Opcion(db.Model):
    __tablename__ = 'opciones'
    idOpcion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

roles_por_usuario = db.Table('roles_por_usuario',
    db.Column('idUsuario', db.Integer, db.ForeignKey('usuarios.idUsuario'), primary_key=True),
    db.Column('idRol', db.Integer, db.ForeignKey('roles.idRol'), primary_key=True)
)

opciones_por_rol = db.Table('opciones_por_rol'),
    db.Column('idRol', db.Integer, db.ForeignKey('roles.idRol'), primary_key=True),
    db.Column('idOpcion', db.Integer, db.ForeignKey('opciones.idOpcion'), primary key=True)
)
