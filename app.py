from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://ADMINMH:Marlon123@PC-DEV36/ProyectoUsuarios?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://ADMINMH:ADMINMH@DESKTOP-HMS6GDC/ProyectoUsuarios?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'clave_secreta_para_sesiones'

db = SQLAlchemy(app)

class Productos(db.Model):
    __tablename__ = 'productos'
    idProductos = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

class Rol(db.Model):
    __tablename__ = 'roles'
    idRol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(50), nullable=True)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    idUsuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    idRol = db.Column(db.Integer, db.ForeignKey('roles.idRol'), nullable=True)
    rol = db.relationship('Rol', backref='usuarios')

class Opcion(db.Model):
    __tablename__ = 'opciones'
    idOpcion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)


def autenticar_usuario(login, password):
    try:
        sp = text("EXEC sp_AutenticarUsuario :login, :password")
        result = db.session.execute(sp, {'login': login, 'password': password})
        user = result.fetchone() 

        if user:
            return {
                'nombre': user.nombre,
                'apellido': user.apellido,
                'idRol': user.idRol,
                'login': user.login
            }
        else:
            return None
    except Exception as e:
        return str(e)

def cambiar_conexion_por_rol(login, password):
    nueva_uri = f'mssql+pyodbc://{login}:{password}@DESKTOP-HMS6GDC/ProyectoUsuarios?driver=ODBC+Driver+17+for+SQL+Server'
    #nueva_uri = f'mssql+pyodbc://{login}:{password}@PC-DEV36/ProyectoUsuarios?driver=ODBC+Driver+17+for+SQL+Server'
    app.config['SQLALCHEMY_DATABASE_URI'] = nueva_uri
    
    db.session.remove() 
    db.engine.dispose() 

    print(f"Conexión actualizada para el usuario: {login}")

def obtener_permisos(login):
    permisos = []
    try:
        sql = text("EXEC sp_GetPermisos :nombre_usuario")
        result = db.session.execute(sql, {"nombre_usuario": login})
        for row in result:
            permisos.append(row[0])
        print(permisos)

    except Exception as e:
        print(f"Error al obtener permisos: {e}")

    return permisos


@app.route('/menu', methods=['GET', 'POST'])
def menu():
    return render_template('menu.html')

@app.route('/productos', methods=['GET', 'POST'])
def productos():
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))

    user = session['usuarioSesion']
    permisos = user.get('permisos', [])
    
    if request.method == 'POST':
        if 'Crear' in permisos or 'Editar' in permisos:
            if 'id' in request.form:  
                producto = Productos.query.get(request.form['id'])
                if producto:
                    producto.nombre = request.form['nombre']
                    producto.precio = request.form['precio']
                    db.session.commit()
                    print("Producto actualizado exitosamente.")
            else:  
                if 'Crear' in permisos:
                    nuevo_producto = Productos(nombre=request.form['nombre'], precio=request.form['precio'])
                    db.session.add(nuevo_producto)
                    db.session.commit()
                    print("Producto agregado exitosamente.")
        else:
            print("No tienes permiso para agregar o editar productos.")
        
        return redirect(url_for('productos'))

    productos = Productos.query.all()
    return render_template('productos.html', productos=productos)

@app.route('/roles', methods=['GET', 'POST'])
def roles():
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))

    user = session['usuarioSesion']
    permisos = user.get('permisos', [])
    
    if request.method == 'POST':
        # Manejo de actualización o creación de rol
        if 'id' in request.form:  
            rol = Rol.query.get(request.form['id'])
            if rol:
                rol.nombre = request.form['nombre']
                rol.descripcion = request.form['descripcion']
                db.session.commit()
                print("Rol actualizado exitosamente.")
        else:  
            if 'Crear' in permisos:
                nuevo_rol = Rol(nombre=request.form.get('nombre'), descripcion=request.form.get('descripcion'))
                db.session.add(nuevo_rol)
                db.session.commit()
                print("Rol agregado exitosamente.")

        return redirect(url_for('roles'))

    roles = Rol.query.all()
    opciones = Opcion.query.all() # Función para obtener las opciones disponibles
    return render_template('roles.html', roles=roles, opciones=opciones)

@app.route('/otorgar_permisos', methods=['POST'])
def otorgar_permisos():
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))

    print('usuarioSesion')
    id_usuario = request.form.get('rol_id')  # ID del rol
    tabla = request.form.get('tabla')  # Nombre de la tabla
    permisos_seleccionados = request.form.getlist('permisos')  # Permisos seleccionados

    for permiso in permisos_seleccionados:
        if permiso == 'Insertar':
            sql = text("EXEC sp_PermisosEspecialesInsertar :idUsuario, :tabla")
            db.session.execute(sql, {'idUsuario': id_usuario, 'tabla': tabla})
            print("Permiso de insertar otorgado exitosamente.")
        elif permiso == 'Eliminar':
            sql = text("EXEC sp_PermisosEspecialesDelete :idUsuario, :tabla")
            db.session.execute(sql, {'idUsuario': id_usuario, 'tabla': tabla})
            print("Permiso de eliminar otorgado exitosamente.")
        elif permiso == 'Seleccionar':
            sql = text("EXEC sp_PermisosEspecialesSelect :idUsuario, :tabla")
            db.session.execute(sql, {'idUsuario': id_usuario, 'tabla': tabla})
            print("Permiso de seleccionar otorgado exitosamente.")
        elif permiso == 'Actualizar':
            sql = text("EXEC sp_PermisosEspecialesUpdate :idUsuario, :tabla")
            db.session.execute(sql, {'idUsuario': id_usuario, 'tabla': tabla})
            print("Permiso de actualizar otorgado exitosamente.")

    db.session.commit()
    return redirect(url_for('roles'))

@app.route('/roles/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_rol(id):
    user = session['usuarioSesion']
    permisos = user.get('permisos', [])
    
    if 'Eliminar' in permisos: 
        rol = Rol.query.get_or_404(id)
        db.session.delete(rol)
        db.session.commit()
        flash("Producto eliminado exitosamente.")
    else:
        print("No tienes permiso para eliminar productos.")
    
    return redirect(url_for('roles'))

@app.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))

    user = session['usuarioSesion']
    permisos = user.get('permisos', [])
    
    if request.method == 'POST':
        if 'Crear' in permisos or 'Editar' in permisos:
            if 'id' in request.form:  
                usuario = Usuario.query.get(request.form['id'])  # Cambié Rol a Usuario
                if usuario:
                    usuario.nombre = request.form['nombre']
                    usuario.apellido = request.form['apellido']
                    usuario.email = request.form['email']
                    db.session.commit()
                    print("Usuario actualizado exitosamente.")
            else:  
                if 'Crear' in permisos:
                    nuevo_usuario = Usuario(
                        nombre=request.form.get('nombre'),
                        apellido=request.form.get('apellido'),
                        email=request.form.get('email'),
                        # Agrega más campos si es necesario
                    )
                    db.session.add(nuevo_usuario)
                    db.session.commit()
                    print("Usuario agregado exitosamente.")
        else:
            print("No tienes permiso para agregar o editar usuarios.")
        
        return redirect(url_for('usuarios'))

    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar_usuario(id):
    user = session['usuarioSesion']
    permisos = user.get('permisos', [])
    
    if 'Eliminar' in permisos: 
        usuario = Usuario.query.get_or_404(id)  # Cambié Rol a Usuario
        db.session.delete(usuario)
        db.session.commit()
        flash("Usuario eliminado exitosamente.")
    else:
        print("No tienes permiso para eliminar usuarios.")
    
    return redirect(url_for('usuarios'))

@app.route('/usuarios/asociar_rol/<int:id>', methods=['GET', 'POST'])
def asociar_rol(id):
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))

    user = session['usuarioSesion']
    permisos = user.get('permisos', [])

    if request.method == 'POST':
        if 'Editar' in permisos:  # Verificamos si el usuario tiene permiso para asociar roles
            rol_id = request.form.get('rol')  # Obtener el rol seleccionado del combo box

            # Ejecutar el procedimiento almacenado para asociar el rol al usuario
            try:
                sp = text("EXEC sp_AsociarRolAUsuario :idUsuario, :idRol")
                db.session.execute(sp, {'idUsuario': id, 'idRol': rol_id})
                db.session.commit()
                flash("Rol asociado exitosamente al usuario.")
            except Exception as e:
                db.session.rollback()
                flash(f"Error al asociar el rol: {str(e)}")
        else:
            flash("No tienes permiso para asociar roles.")
        
        return redirect(url_for('usuarios'))

    # Obtener la lista de roles disponibles para el combo box
    roles = Rol.query.all()
    usuario = Usuario.query.get_or_404(id)  # Obtener el usuario seleccionado

    return render_template('asociar_rol.html', usuario=usuario, roles=roles)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('username')
        password = request.form.get('pass')

        user = autenticar_usuario(login, password)
        print(type(user))  # Debería ser <class 'dict'>
        print(user)
        if user:
            session.clear()
            session['usuarioSesion'] = user

            cambiar_conexion_por_rol(login, password)
            permisos = obtener_permisos(login)
            print(permisos)
            user['permisos'] = permisos
            if len(permisos) >= 4:
                return redirect(url_for('dashboardAdmin'))
            
            return redirect(url_for('productos'))
        else:
            flash("Error al iniciar sesión. Credenciales incorrectas.")
    
    return render_template('Login.html')


@app.route('/dashboardAdmin')
def dashboardAdmin():
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))

    
    return render_template('dashboardAdmin.html')

@app.route('/gestionarVentas')
def gestionarVentas():
    if 'usuarioSesion' not in session:
        return redirect(url_for('login'))
    return render_template('dashboardVentas.html')

@app.route('/procesar_datos', methods=['POST'])
def procesar_datos():
    if request.method == 'POST':
        username = request.form.get('username')
        rol = request.form.get('rol')
        permisos = [
            '1' if request.form.get('permisos_agregar') == 'on' else '0',
            '1' if request.form.get('permisos_eliminar') == 'on' else '0',
            '1' if request.form.get('permisos_visualizar') == 'on' else '0',
            '1' if request.form.get('permisos_editar') == 'on' else '0'
        ]

        #TODO: El json es solo para comprobar que si esté mandando los datos XD lo podes quitar si querés
        return jsonify({
            "username": username,
            "rol": rol,
            "permisos": permisos
        })

    return render_template('menu.html')

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    return render_template('registrarse.html')