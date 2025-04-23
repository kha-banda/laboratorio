from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for, session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import pymysql
from io import BytesIO
import os
import textwrap

y_position = 560  # Posición inicial en el eje Y
max_width = 50  # Número máximo de caracteres por línea (ajústalo según el ancho de la página)


app = Flask(__name__)

# --------------------------------- conexionBD ---------------------------------

app.secret_key = 'Alberto970013260M'

def obtener_conexion():
    return pymysql.connect(
        host='69.62.71.171',
        user='root',
        password='caravanadestrucs',
        database='bd_ehrlich',
        cursorclass=pymysql.cursors.DictCursor
    )

# --------------------------------- Rutas ---------------------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

#sesion del administrador
@app.route('/home')
def home():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('home.html', usuario=usuario)
    else:
        return redirect(url_for('login'))


#sesion de graficas
@app.route('/estadisticas')
def estadisticas():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('estadisticas.html', usuario=usuario)
    else:
        return redirect(url_for('login'))

# --------------------------------- Funciones ---------------------------------

def consultar_estudios():
        # Establecer la conexión con la base de datos MySQL
    connection = obtener_conexion()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT nombre, precio FROM estudio;"
            cursor.execute(sql)
            resultado = cursor.fetchall()
            print("hace consulta de estudios")
    finally:        
            connection.close()
    return resultado

def genera_reporte(fecha_inicio):
    connection = obtener_conexion()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM cliente WHERE fecha >= %s"
            cursor.execute(sql, (fecha_inicio,))
            resultado = cursor.fetchall()
    finally:        
            connection.close()
    return resultado

# --------------------------------- Rutas de get y post ---------------------------------

#sesion del trabajador
@app.route('/student', methods=['GET', 'POST'])
def student():
    connection = obtener_conexion()
    if request.method == 'GET':
        if 'usuario' in session:
            usuario = session['usuario']
            estudios = consultar_estudios()
            #reporte = genera_reporte(datetime.now().date() - timedelta(days=datetime.now().date().weekday()))
            #no_registros = True
            return render_template('student.html', usuario=usuario, estudios=estudios)
        else:
            return redirect(url_for('login'))
    
    elif request.method == 'POST':
        if 'nombre_completo' in request.form:  # Esto verifica si el formulario es de cliente
            connection = obtener_conexion()
            print("Datos recibidos:", request.form) 
            nombre_completo = request.form.get('nombre_completo')
            direccion = request.form.get('direccion')
            correo = request.form.get('correo')
            numero_telefonico = request.form.get('numero_telefonico')
            genero = request.form.get('genero')
            observaciones = request.form.get('observaciones')
            fecha_solicitud_str = request.form.get('fecha_solicitud')
            importe = request.form.get('Importe')
            abona = request.form.get('Adeudo')
            estudios_seleccionados = request.form.get('estudiosSeleccionados')
            estudios_seleccionados = estudios_seleccionados if estudios_seleccionados else None
            factura_cliente = request.form.get('RFC')
            #Se agregaron lo que es el nombre del medico y el descuento total que se realiza al cliente
            medico = request.form.get('nombre_medico')
            descuento =  request.form.get('Descuento')
            

            fecha_solicitud = datetime.strptime(fecha_solicitud_str, '%Y-%m-%d').date()

            try:
                #Se convierten en cadenas para poder pasar a insertar en la BD
                importe2 = float(importe)
                abona2 = float(abona)
                adeudo = float(importe2 - abona2)
                
                with connection.cursor() as cursor:
                    #Falta agregar el nombre del médico a la tabla de estudios
                    sql = "INSERT INTO cliente (nombre, direccion, correo, telefono, genero, observaciones, medico, fecha, adeudo, pago_total, abono, array_estudios, RFC) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (nombre_completo, direccion, correo, numero_telefonico, genero, observaciones, medico, fecha_solicitud, adeudo, importe, abona, estudios_seleccionados, factura_cliente))
                    connection.commit()
                    #return render_template('exito.html', mensaje='Registro exitoso')
            except Exception as e:
                print(f"Error al insertar en la base de datos: {e}")
                #return render_template('error.html', mensaje='Error en la base de datos')

            # Devolver el archivo PDF como respuesta
            response = generar_archivo_pdf(nombre_completo, direccion, correo, numero_telefonico, genero, observaciones, fecha_solicitud, medico, adeudo, importe, estudios_seleccionados, descuento)
            return response
        
        elif 'nombreProducto' in request.form:
            nombre = request.form.get('nombreProducto')
            cantidad = request.form.get('cantidadProducto')
            marca = request.form.get('marcaProducto')
            fecha_ingreso_str = request.form.get('fechaIngreso')
            if fecha_ingreso_str:
                fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d').date()
            else:
                fecha_ingreso = None  # Manejo de caso donde la fecha no está presente
            try:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO producto (nombre, cantidad, marca, fecha_ingreso) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (nombre, cantidad, marca, fecha_ingreso))
                    connection.commit()
                return "Producto guardado exitosamente"
            except Exception as e:
                print(f"Error al insertar en la base de datos: {e}")
                return "Hubo un error al guardar el producto"
    return render_template('student.html')  # Renderiza el formulario en caso de GET

# Agrega la nueva ruta para obtener el reporte por AJAX
@app.route('/obtener_reporte', methods=['POST'])
def obtener_reporte():
    fecha_inicio_str = request.form.get('fecha_inicio')
    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    reporte = genera_reporte(fecha_inicio)
    return jsonify(reporte)

def generar_archivo_pdf(nombre_completo, direccion, correo, numero_telefonico, genero, observaciones, fecha_solicitud, medico, adeudo, importe, estudios_seleccionados, descuento):
    try:
        adeudo_valor = float(adeudo)
    except (ValueError, TypeError):
        adeudo_valor = 0.0
    saldo_restante = float(importe) - float(adeudo_valor)
    estudios_lista = estudios_seleccionados.split('\r\n')
    #print(estudios_lista)
    # Crear el archivo PDF con reportlab
    response = canvas.Canvas('recibo.pdf', pagesize=letter)      
    # Agregar contenido al archivo PDF
    response.drawString(60, 680, f'     {fecha_solicitud}')
    response.drawString(110, 665, f'     {nombre_completo}')
    response.drawString(100, 650, f'     {medico}') #aqui se añadio medico
    response.drawString(100, 630, f'     {direccion}')
    response.drawString(300, 630, f'{numero_telefonico}')
    #response.drawString(450, 630, f'  XX')
    response.drawString(520, 630, f'{genero}')
    response.drawString(100, 600, f'Correo Electrónico: {correo}') 
    response.drawString(490, 540, f' Resta: {adeudo}') #tenia antes deja se cabmio
    response.drawString(490, 520, f' Deja: {saldo_restante}')
    response.drawString(490, 500, f' Descuento: % {descuento}')#aqui se añadio el descuento
    response.drawString(490, 440, f' Total: {importe}') 
    response.drawString(110, 453, f'Observaciones: {observaciones}')
    response.drawString(100, 580, f' --------------------------------------------------- ')
    y_position = 560  # Posición inicial en el eje Y
    for estudio in estudios_lista:
        wrapped_text = textwrap.wrap(estudio.strip(), width=max_width)  # Dividir el texto
        for line in wrapped_text:
            response.drawString(100, y_position, line)
            y_position -= 20  # Ajusta el espacio entre líneas

        # Si la posición Y es demasiado baja, pasa a una nueva página
            if y_position < 40:
                response.showPage()  # Nueva página
                y_position = 800  # Reiniciar la posición Y
    # Guardar el archivo PDF
    response.save()
    # Retornar el archivo PDF como respuesta
    return send_file('recibo.pdf', as_attachment=True)

    
@app.route('/logout')
def logout():
    # Eliminar la información de la sesión
    session.pop('usuario', None)
    return redirect(url_for('login'))

#Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    connection = obtener_conexion()
    if request.method == 'POST':
        correo = request.form['correo']
        passwd = request.form['contrasena']
        
        try:
            with connection.cursor() as cursor:
                # Consulta para verificar las credenciales del usuario
                query = "SELECT * FROM usuario WHERE correo = %s AND password = %s"
                cursor.execute(query, (correo, passwd))
                usuario = cursor.fetchone()
            if usuario:
                # Si las credenciales son correctas, almacenamos al usuario en la sesión
                session['usuario'] = usuario
                # Ejemplo de cómo manejar diferentes tipos de usuarios
                estudios = consultar_estudios()
                # Si es tipo 0 es usuario Administrador
                if usuario['tipo'] == 0:
                    #Se deben pasar la tabla cliente, estudio, producto y usuarios para su modificación como Administrador
                    return render_template('home.html', usuario=usuario)
                # Si es tipo 0 es usuario Trabajador
                elif usuario['tipo'] == 1:
                    estudios = consultar_estudios()
                    #Unicamente se pasa los estudios para generar los reportes o las recibos
                    return render_template('student.html', usuario=usuario, estudios=estudios)
            else:
                # Si no se encontró ningún usuario con esas credenciales
                mensaje_error = 'Credenciales incorrectas. Inténtalo de nuevo.'
                return render_template('login.html', mensaje_error=mensaje_error)
        except pymysql.Error as e:
            # Manejo de errores de conexión o consulta
            print(f"Error al ejecutar la consulta: {e}")
            mensaje_error = 'Error en la base de datos. Inténtalo más tarde.'
            return render_template('login.html', mensaje_error=mensaje_error)
    # Si no se envió un formulario POST (por ejemplo, al acceder a la página de inicio de sesión)
    return render_template('login.html')

# -----------------------------------------------
# OBTENER USUARIOS ACCDEDIENDO A LA BASE DE DATOS
# -----------------------------------------------
def obtener_usuarios():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuario")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return usuarios

@app.route('/usuarios')
def usuarios():
    usuarios = obtener_usuarios()
    return jsonify(usuarios)

# -----------------------------------------------
# OBTENER PRODUCTOS ACCDEDIENDO A LA BASE DE DATOS
# -----------------------------------------------
def obtener_productos():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM producto")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return productos

@app.route('/productos')
def productos():
    productos = obtener_productos()
    return jsonify(productos)

# -----------------------------------------------
# OBTENER CLIENTES ACCDEDIENDO A LA BASE DE DATOS
# -----------------------------------------------
def obtener_clientes():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cliente")
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return clientes

@app.route('/clientesBD')
def clientesBD():
    clientes = obtener_clientes()
    #print(clientes)
    return jsonify(clientes)

# -----------------------------------------------
# OBTENER ESTUDIOS ACCDEDIENDO A LA BASE DE DATOS
# -----------------------------------------------
def obtener_estudios():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estudio")
    estudios = cursor.fetchall()
    cursor.close()
    conn.close()
    return estudios

@app.route('/estudiosBD')
def estudiosBD():
    estudios = obtener_estudios()
    #print(clientes)
    return jsonify(estudios)

#############################################################################
##############################################################################

@app.route('/usuarios/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuario WHERE id_usuario = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Usuario eliminado correctamente'})

@app.route('/actualizar-usuario', methods=['POST'])
def actualizar_usuario():
    try:
        json_data = request.get_json()
        #print(f"Datos JSON recibidos: {json_data}") 
        id_usuario = int(json_data['idUsuarioEditar']) #Convertimos el id_usuario en entero desde el formulario
        #print(f"ID del usuario a actualizar: {id_usuario}")  # Agrega esto para depurar
        nombre = json_data['nombreUsuarioEditar']
        correo = json_data['correoUsuarioEditar']
        telefono = json_data['telefonoUsuarioEditar']
        #apellido = request.form.get('apellidoUsuarioEditar')
        #password = request.form.get('passwordUsuarioEditar')
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
        # Verificar si el usuario existe
            cursor.execute("SELECT * FROM usuario WHERE id_usuario=%s", (id_usuario,))
            usuario_existente = cursor.fetchone()
            if not usuario_existente:
                return jsonify({'message': 'Usuario no encontrado'}), 404            
            sql = """
                UPDATE usuario 
                SET nombre=%s, correo=%s, telefono=%s 
                WHERE id_usuario=%s
            """
            cursor.execute(sql, (nombre, correo, telefono, id_usuario))
            conexion.commit()
        conexion.close()
        print("Usuario actualizado exitosamente")
        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    except Exception as e:
        print(f"Error al actualizar el usuario: {e}")
        return jsonify({'message': 'Hubo un error al actualizar el usuario'}), 500

@app.route('/agregarUsuario', methods=['POST'])
def agregar_usuario():
    nombre = request.form['nombreUsuario']
    apellido = request.form['apellidoUsuario']
    correo = request.form['correoUsuario']
    password = request.form['passwordUsuario']
    telefono = request.form['telefonoUsuario']
    
    # Convertir tipoUsuario a entero
    tipo = int(request.form['tipoUsuario'])  # Convertimos a entero
    
    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute(
            "INSERT INTO usuario (nombre, apellido, correo, password, tipo, telefono) VALUES (%s, %s, %s, %s, %s, %s)",
            (nombre, apellido, correo, password, tipo, telefono)
        )
    conexion.commit()
    conexion.close()
    return jsonify({'message': 'Usuario agregado exitosamente'}), 200

@app.route('/clientes/<int:id_cliente>', methods=['PUT'])
def actualizar_adeudo_cliente(id_cliente):
    try:
        # Obtener el nuevo valor de adeudo desde el cuerpo JSON de la solicitud
        nuevo_adeudo = request.json['adeudo']
        # Establecer conexión a la base de datos
        conexion = obtener_conexion()
        # Crear cursor para ejecutar la consulta SQL
        with conexion.cursor() as cursor:
            # Consulta SQL para actualizar el adeudo del cliente
            sql = "UPDATE cliente SET adeudo = %s WHERE id_cliente = %s"
            cursor.execute(sql, (nuevo_adeudo, id_cliente))
        # Confirmar la transacción
        conexion.commit()
        # Cerrar la conexión
        conexion.close()
        print(f"Adeudo actualizado correctamente para el cliente {id_cliente}")
        # Retornar una respuesta exitosa
        return jsonify({'message': f'Adeudo actualizado correctamente para el cliente {id_cliente}'}), 200
    except Exception as e:
        # En caso de error, retornar un mensaje de error
        return jsonify({'error': str(e)}), 500

@app.route('/actualizar-cliente', methods=['POST'])
def actualizar_cliente():
    try:
        json_data = request.get_json()
        #print(f"Datos JSON recibidos: {json_data}") 
        id_cliente = int(json_data['idClienteEditar']) #Convertimos el id_usuario en entero desde el formulario
        #print(f"ID del usuario a actualizar: {id_usuario}")  # Agrega esto para depurar
        nombre = json_data['nombreClienteEditar']
        correo = json_data['correoClienteEditar']
        telefono = json_data['telefonoClienteEditar']
        medico = json_data['medicoClienteEditar']
        #apellido = request.form.get('apellidoUsuarioEditar')
        #password = request.form.get('passwordUsuarioEditar')
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
        # Verificar si el usuario existe
            cursor.execute("SELECT * FROM cliente WHERE id_cliente=%s", (id_cliente,))
            cliente_existente = cursor.fetchone()
            if not cliente_existente:
                return jsonify({'message': 'Cliente no encontrado en Python'}), 404            
            sql = """
                UPDATE cliente 
                SET nombre=%s, correo=%s, telefono=%s, medico=%s 
                WHERE id_cliente=%s
            """
            cursor.execute(sql, (nombre, correo, telefono, medico, id_cliente))
            conexion.commit()
        conexion.close()
        print("Cliente actualizado exitosamente. Python")
        return jsonify({'message': 'Usuario actualizado exitosamente Python'}), 200
    except Exception as e:
        print(f"Error al actualizar el usuario: {e}")
        return jsonify({'message': 'Hubo un error al actualizar el usuario Python'}), 500

@app.route('/actualizar-estudio', methods=['POST'])
def actualizar_estudio():
    try:
        json_data = request.get_json()
        #print(f"Datos JSON recibidos: {json_data}") 
        id_estudio = int(json_data['idEstudioEditar']) #Convertimos el id_usuario en entero desde el formulario
        #print(f"ID del usuario a actualizar: {id_usuario}")  # Agrega esto para depurar
        nombre = json_data['nombreEstudioEditar']
        folio = json_data['folioEstudioEditar']
        precio = json_data['precioEstudioEditar']
        descuento = json_data['descuentoEstudioEditar']
        #apellido = request.form.get('apellidoUsuarioEditar')
        #password = request.form.get('passwordUsuarioEditar')
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
        # Verificar si el usuario existe
            cursor.execute("SELECT * FROM estudio WHERE id_estudio=%s", (id_estudio,))
            estudio_existente = cursor.fetchone()
            if not estudio_existente:
                return jsonify({'message': 'Estudio no encontrado en Python'}), 404            
            sql = """
                UPDATE estudio 
                SET nombre=%s, folio=%s, precio=%s, descuento=%s 
                WHERE id_estudio=%s
            """
            cursor.execute(sql, (nombre, folio, precio, descuento, id_estudio))
            conexion.commit()
        conexion.close()
        print("Estudio actualizado exitosamente. Python")
        return jsonify({'message': 'Estudio actualizado exitosamente Python'}), 200
    except Exception as e:
        print(f"Error al actualizar el estudio: {e}")
        return jsonify({'message': 'Hubo un error al actualizar el estudio Python'}), 500

@app.route('/agregarEstudio', methods=['POST'])
def agregar_estudio():
    nombre = request.form['nombreEstudio']
    folio = request.form['folioEstudio']
    precio = request.form['precioEstudio']
    descuento = request.form['descuentoEstudio']
    conexion = obtener_conexion()
    with conexion.cursor() as cursor:
        cursor.execute(
            "INSERT INTO estudio (nombre, folio, precio, descuento) VALUES (%s, %s, %s, %s)",
            (nombre, folio, precio, descuento)
        )
    conexion.commit()
    conexion.close()
    return jsonify({'message': 'Estudio agregado exitosamente Python'}), 200

@app.route('/eliminar-estudio/<int:id_estudio>', methods=['DELETE'])
def eliminar_estudio(id_estudio):
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            sql = "DELETE FROM estudio WHERE id_estudio = %s"
            cursor.execute(sql, (id_estudio,))
            conexion.commit()
        conexion.close()

        print("Producto eliminado exitosamente")
        return jsonify({'message': 'Producto eliminado exitosamente'}), 200
    except Exception as e:
        print(f"Error al eliminar el producto: {e}")
        return jsonify({'message': 'Hubo un error al eliminar el producto for Python'}), 500    

@app.route('/actualizar-producto', methods=['POST'])
def actualizar_producto():
    try:
        jason_data = request.get_json(force=True)
        id_producto = jason_data.get('idProductoEditar')
        nombre = jason_data.get('nombreProductoEditar')
        cantidad = jason_data.get('cantidadProductoEditar')
        marca = jason_data.get('marcaProductoEditar')
        precio = jason_data.get('precioProductoEditar')
        #fecha_ingreso = jason_data.get('fechaProductoEditar')
        print("Python -- Datos recibidos: id_producto={id_producto}, nombre={nombre}, cantidad={cantidad}, marca={marca}, precio={precio}")
        print("Python -- Datos JSON recibidos:", jason_data)
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # nombre varchar, cantidad int, marca varchar, precio float
            sql = "UPDATE producto SET nombre=%s, cantidad=%s, marca=%s, precio=%s WHERE id_producto=%s"
            cursor.execute(sql, (nombre, cantidad, marca, precio, id_producto))
            conexion.commit()
        conexion.close()

        print("Pyton --Producto actualizado exitosamente")
        return jsonify({'message': 'Producto actualizado exitosamente'}), 200
    except Exception as e:
        print(" Python Error al actualizar el producto: {e}")
        return jsonify({'message': 'Python Hubo un error al actualizar el producto'}), 500

@app.route('/agregar-producto', methods=['POST'])
def agregar_producto():
    try:
        jason_data = request.get_json(force=True)
        #id_producto = jason_data.get('idProductoEditar')
        nombre = jason_data.get('nombreProductoEditar')
        cantidad = jason_data.get('cantidadProductoEditar')
        marca = jason_data.get('marcaProductoEditar')
        precio = jason_data.get('precioProductoEditar')
        fecha_ingreso = jason_data.get('fechaProductoEditar')
        print("Python -- Datos recibidos: nombre={nombre}, cantidad={cantidad}, marca={marca}, precio={precio}, fecha={fecha_ingreso}")

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            # nombre varchar, cantidad int, marca varchar, precio float
            sql = "INSERT INTO producto (nombre, cantidad, marca, precio, fecha_ingreso) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nombre, cantidad, marca, precio, fecha_ingreso))
            conexion.commit()
        conexion.close()

        print("MSG Python - Producto agregado exitosamente")
        return jsonify({'message': 'Producto agregado exitosamente'}), 200
    except Exception as e:
        print(f"Error al agregar el producto: {e}")
        return jsonify({'message': 'Hubo un error al agregar el producto'}), 500
#función del administrador
@app.route('/borrar-producto', methods=['DELETE'])
def borrar_producto():
    try:
        json_data = request.get_json(force=True)
        id_producto = json_data.get('idProductoBorrar')
        
        if not id_producto:
            return jsonify({'message': 'ID de producto no proporcionado for Python'}), 400

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            sql = "DELETE FROM producto WHERE id_producto = %s"
            cursor.execute(sql, (id_producto,))
            conexion.commit()
        conexion.close()

        print(f"Python -- Producto con ID {id_producto} borrado exitosamente")
        return jsonify({'message': 'Producto borrado exitosamente for Python'}), 200
    except Exception as e:
        print(f"Python -- Error al borrar el producto: {e}")
        return jsonify({'message': 'Hubo un error al borrar el producto for Python'}), 500
#función de borrado del usuario
@app.route('/eliminar-producto/<int:id_producto>', methods=['DELETE'])
def eliminar_producto(id_producto):
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            sql = "DELETE FROM producto WHERE id_producto = %s"
            cursor.execute(sql, (id_producto,))
            conexion.commit()
        conexion.close()

        print("Producto eliminado exitosamente")
        return jsonify({'message': 'Producto eliminado exitosamente'}), 200
    except Exception as e:
        print(f"Error al eliminar el producto: {e}")
        return jsonify({'message': 'Hubo un error al eliminar el producto'}), 500


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(debug=True)