from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import (
    UserProfile, Recurso, CategoriaRecurso, FormularioContacto, RespuestaConsulta,
    CategoriaForo, HiloForo, RespuestaForo
)
from .forms import RecursoForm, UserForm, UserProfileForm


def custom_login(request):
    if request.user.is_authenticated:
        return redirigir_segun_tipo_usuario(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirigir_segun_tipo_usuario(user)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'miapp/login.html')

def redirigir_segun_tipo_usuario(user):
    try:
        if hasattr(user, 'userprofile'):
            if user.userprofile.tipo_usuario == 'admin':
                return redirect('miapp:admin_dashboard')
            elif user.userprofile.tipo_usuario == 'pasante':
                return redirect('miapp:pasante_dashboard')
        return redirect('miapp:index')
    except UserProfile.DoesNotExist:
        return redirect('miapp:index')

def custom_logout(request):
    logout(request)
    return redirect('miapp:login')

@login_required
def mi_perfil(request):
    """Vista para mostrar el perfil del usuario"""
    user_profile = request.user.userprofile
    
    # Obtener nombre completo
    nombre_completo = obtener_nombre_completo(request.user)
    
    # Estadísticas del usuario
    stats = {
        'total_consultas': FormularioContacto.objects.filter(usuario=request.user).count(),
        'consultas_respondidas': FormularioContacto.objects.filter(usuario=request.user, respondido=True).count(),
        'hilos_creados': HiloForo.objects.filter(creado_por=request.user).count(),
        'respuestas_creadas': RespuestaForo.objects.filter(creado_por=request.user).count(),
    }
    
    # Consultas recientes del usuario
    consultas_recientes = FormularioContacto.objects.filter(
        usuario=request.user
    ).order_by('-creado_en')[:5]
    
    # Hilos recientes del usuario
    hilos_recientes = HiloForo.objects.filter(
        creado_por=request.user
    ).order_by('-creado_en')[:5]
    
    context = {
        'user_profile': user_profile,
        'nombre_completo': nombre_completo,
        'stats': stats,
        'consultas_recientes': consultas_recientes,
        'hilos_recientes': hilos_recientes,
    }
    
    return render(request, 'miapp/mi_perfil.html', context)

def obtener_nombre_completo(user):
    """Función auxiliar para obtener el nombre completo del usuario"""
    # Intentar obtener de UserProfile si existe
    if hasattr(user, 'userprofile'):
        user_profile = user.userprofile
        # Verificar si tiene primer_nombre y primer_apellido
        if hasattr(user_profile, 'primer_nombre') and user_profile.primer_nombre:
            nombre = user_profile.primer_nombre
            apellido = user_profile.primer_apellido if hasattr(user_profile, 'primer_apellido') and user_profile.primer_apellido else ""
            if nombre and apellido:
                return f"{nombre} {apellido}"
            elif nombre:
                return nombre
    
    # Si no hay en UserProfile, intentar con los campos estándar de User
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        # Si no hay nombre, usar el username
        return user.username

def index(request):
    return render(request, 'miapp/index.html')

@login_required
def datos_curiosos(request):
    return render(request, 'miapp/datos_curiosos.html')

@login_required
def recursos(request):
    recursos_list = Recurso.objects.filter(es_publico=True)
    return render(request, 'miapp/recursos.html', {'recursos': recursos_list})

@login_required
def recursos_multimedia(request):
    recursos_list = Recurso.objects.filter(es_publico=True)
    return render(request, 'miapp/recursos_multimedia.html', {'recursos': recursos_list})

@login_required
def tests_psicologicos(request):
    return render(request, 'miapp/tests.html')

@login_required
def formulario_contacto(request):
    # Para PACIENTES: solo sus consultas
    # Para ADMIN/PASANTES: todas las consultas
    if hasattr(request.user, 'userprofile'):
        if request.user.userprofile.es_paciente():
            consultas_usuario = FormularioContacto.objects.filter(usuario=request.user).order_by('-creado_en')
        else:  # Admin o Pasante - ven todas las consultas
            consultas_usuario = FormularioContacto.objects.all().order_by('-creado_en')
    else:
        consultas_usuario = None
    
    if request.method == 'POST':
        tipo_consulta = request.POST.get('tipo_consulta')
        asunto = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')
        
        FormularioContacto.objects.create(
            usuario=request.user,
            tipo_consulta=tipo_consulta,
            asunto=asunto,
            mensaje=mensaje
        )
        messages.success(request, 'Tu consulta ha sido enviada correctamente.')
        return redirect('miapp:formulario_contacto')
    
    return render(request, 'miapp/formulario_contacto.html', {
        'consultas_usuario': consultas_usuario
    })

# ==================== DASHBOARDS ====================

@login_required
def admin_dashboard(request):
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_admin():
        messages.error(request, 'No tienes permisos para acceder al dashboard de administrador')
        return redirect('miapp:index')
    
    context = {
        'user': request.user,
        'stats': {
            'total_usuarios': User.objects.count(),
            'total_recursos': Recurso.objects.count(),
            'total_consultas': FormularioContacto.objects.count(),
            'consultas_sin_responder': FormularioContacto.objects.filter(respondido=False).count(),
        }
    }
    return render(request, 'miapp/admin/dashboard.html', context)

@login_required
def pasante_dashboard(request):
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_pasante():
        messages.error(request, 'No tienes permisos para acceder al dashboard de pasante')
        return redirect('miapp:index')
    
    context = {
        'user': request.user,
        'stats': {
            'total_recursos': Recurso.objects.count(),
            'total_consultas': FormularioContacto.objects.count(),
            'consultas_sin_responder': FormularioContacto.objects.filter(respondido=False).count(),
        }
    }
    return render(request, 'miapp/pasante/dashboard.html', context)

# ==================== ADMINISTRACIÓN ====================

@login_required
def admin_gestion_usuarios(request):
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_admin():
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('miapp:index')
    
    usuarios = User.objects.all().select_related('userprofile')

    if request.method == 'POST':
        print("POST DATA:", request.POST)

        # ===========================
        # CREAR USUARIO
        # ===========================
        if 'crear_usuario' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            tipo_usuario = request.POST.get('tipo_usuario')

            # Validar duplicado
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe')
                return redirect('miapp:admin_gestion_usuarios')

            try:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email
                )
                user.userprofile.tipo_usuario = tipo_usuario
                user.userprofile.save()

                messages.success(request, f'Usuario {username} creado exitosamente')

            except Exception as e:
                messages.error(request, f"Error al crear usuario: {e}")

            return redirect('miapp:admin_gestion_usuarios')

        # ===========================
        # EDITAR USUARIO
        # ===========================
        elif 'editar_usuario' in request.POST:
            user_id = request.POST.get('user_id')
            username = request.POST.get('username')
            email = request.POST.get('email')
            tipo_usuario = request.POST.get('tipo_usuario')
            is_active = request.POST.get('is_active') == 'on'

            user = get_object_or_404(User, id=user_id)

            # ==== Validar nombre duplicado ====
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, f'El nombre de usuario "{username}" ya está en uso.')
                return redirect('miapp:admin_gestion_usuarios')

            # ==== Validar email duplicado (opcional) ====
            if email and User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, f'El correo "{email}" ya está en uso.')
                return redirect('miapp:admin_gestion_usuarios')

            try:
                # Actualizar User
                user.username = username
                user.email = email
                user.is_active = is_active
                user.save()

                # Actualizar Profile
                user.userprofile.tipo_usuario = tipo_usuario
                user.userprofile.save()

                messages.success(request, f'Usuario {user.username} actualizado correctamente')

            except Exception as e:
                messages.error(request, f"Error al actualizar usuario: {e}")

            return redirect('miapp:admin_gestion_usuarios')

        # ===========================
        # ELIMINAR USUARIO
        # ===========================
        elif "eliminar_usuario" in request.POST:
            user_id = request.POST.get("eliminar_user_id")

            try:
                usuario = get_object_or_404(User, pk=user_id)
                usuario.delete()
                messages.success(request, "Usuario eliminado correctamente")

            except Exception as e:
                messages.error(request, f"Error al eliminar usuario: {e}")

            return redirect('miapp:admin_gestion_usuarios')

  
    return render(request, 'miapp/admin/gestion_usuarios.html', {
        'usuarios': usuarios
    })
    
@login_required
def admin_gestion_recursos(request):
    """
    Gestión de recursos para ADMIN:
    - Soporta campos: titulo, descripcion, tipo_recurso, categoria, url, archivo, portada, contenido, es_publico
    - Validación: debe existir url o archivo al crear
    """
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_admin():
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('miapp:index')
    
    recursos_list = Recurso.objects.all().select_related('categoria', 'creado_por')
    categorias = CategoriaRecurso.objects.all()
    
    if request.method == 'POST':
        # Crear recurso
        if 'crear_recurso' in request.POST:
            titulo = request.POST.get('titulo', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            tipo_recurso = request.POST.get('tipo_recurso')
            categoria_id = request.POST.get('categoria')
            contenido = request.POST.get('contenido', '').strip()
            es_publico = request.POST.get('es_publico') == 'on'
            url = request.POST.get('url', '').strip()
            archivo = request.FILES.get('archivo')
            portada = request.FILES.get('portada')
            
            # Validaciones básicas
            if not titulo or not descripcion or not categoria_id:
                messages.error(request, 'Por favor completa todos los campos obligatorios (Título, Descripción, Categoría).')
                return redirect('miapp:admin_gestion_recursos')
            
            # Requerir al menos url o archivo
            if not url and not archivo:
                messages.error(request, 'Debes proporcionar un ENLACE (URL) o subir un ARCHIVO.')
                return redirect('miapp:admin_gestion_recursos')
            
            try:
                recurso = Recurso.objects.create(
                    titulo=titulo,
                    descripcion=descripcion,
                    tipo_recurso=tipo_recurso,
                    categoria_id=categoria_id,
                    contenido=contenido,
                    es_publico=es_publico,
                    url=url if url else None,
                    archivo=archivo if archivo else None,
                    portada=portada if portada else None,
                    creado_por=request.user
                )
                messages.success(request, f'Recurso "{titulo}" creado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al crear recurso: {e}')
            
            return redirect('miapp:admin_gestion_recursos')
        
        # Editar recurso
        elif 'editar_recurso' in request.POST:
            recurso_id = request.POST.get('recurso_id')
            recurso = get_object_or_404(Recurso, id=recurso_id)
            
            titulo = request.POST.get('titulo', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            tipo_recurso = request.POST.get('tipo_recurso')
            categoria_id = request.POST.get('categoria')
            contenido = request.POST.get('contenido', '').strip()
            es_publico = request.POST.get('es_publico') == 'on'
            url = request.POST.get('url', '').strip()
            archivo = request.FILES.get('archivo')
            portada = request.FILES.get('portada')
            
            # Validaciones básicas
            if not titulo or not descripcion or not categoria_id:
                messages.error(request, 'Por favor completa todos los campos obligatorios (Título, Descripción, Categoría).')
                return redirect('miapp:admin_gestion_recursos')
            
            # Si no existe url ni archivo nuevo ni archivo previo -> rechazar
            if not url and not archivo and not recurso.archivo:
                messages.error(request, 'El recurso debe tener un ENLACE (URL) o un ARCHIVO. Si quieres eliminar el archivo existente primero sube otro o añade una URL.')
                return redirect('miapp:admin_gestion_recursos')
            
            try:
                recurso.titulo = titulo
                recurso.descripcion = descripcion
                recurso.tipo_recurso = tipo_recurso
                recurso.categoria_id = categoria_id
                recurso.contenido = contenido
                recurso.es_publico = es_publico
                recurso.url = url if url else None
                
                # Reemplazar archivo si se sube uno nuevo
                if archivo:
                    recurso.archivo = archivo
                # Reemplazar portada si se sube una nueva
                if portada:
                    recurso.portada = portada
                
                recurso.save()
                messages.success(request, f'Recurso "{titulo}" actualizado')
            except Exception as e:
                messages.error(request, f'Error al actualizar recurso: {e}')
            
            return redirect('miapp:admin_gestion_recursos')
        
        # Eliminar recurso
        elif 'eliminar_recurso' in request.POST:
            recurso_id = request.POST.get('recurso_id')
            recurso = get_object_or_404(Recurso, id=recurso_id)
            titulo = recurso.titulo
            try:
                recurso.delete()
                messages.success(request, f'Recurso "{titulo}" eliminado')
            except Exception as e:
                messages.error(request, f'Error al eliminar recurso: {e}')
            
            return redirect('miapp:admin_gestion_recursos')
    
    return render(request, 'miapp/admin/gestion_recursos.html', {
        'recursos': recursos_list,
        'categorias': categorias
    })

@login_required
def admin_consultas(request):
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_admin():
        messages.error(request, 'No tienes permisos para acceder al dashboard de administrador')
        return redirect('miapp:index')
    
    consultas = FormularioContacto.objects.all().select_related('usuario')
    
    if request.method == 'POST':
        consulta_id = request.POST.get('consulta_id')
        respuesta = request.POST.get('respuesta')
        
        consulta = get_object_or_404(FormularioContacto, id=consulta_id)
        # Crear respuesta usando el nuevo modelo
        RespuestaConsulta.objects.create(
            consulta=consulta,
            respondido_por=request.user,
            respuesta=respuesta
        )
        consulta.respondido = True
        consulta.save()
        messages.success(request, 'Respuesta enviada exitosamente')
    
    return render(request, 'miapp/admin/consultas.html', {'consultas': consultas})

# ==================== PASANTE ====================

@login_required
def pasante_gestion_recursos(request):
    """
    Gestión de recursos para PASANTE:
    Igual que admin, pero solo permite editar/eliminar recursos creados por el pasante.
    """
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_pasante():
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('miapp:index')
    
    recursos_list = Recurso.objects.all().select_related('categoria', 'creado_por')
    categorias = CategoriaRecurso.objects.all()
    
    if request.method == 'POST':

        # ---------------------------------------------------------
        # CREAR RECURSO
        # ---------------------------------------------------------
        if 'crear_recurso' in request.POST:

            titulo = request.POST.get('titulo', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            tipo_recurso = request.POST.get('tipo_recurso')
            categoria_id = request.POST.get('categoria')
            contenido = request.POST.get('contenido', '').strip()
            es_publico = request.POST.get('es_publico') == 'on'

            # COINCIDE CON TU HTML
            url = request.POST.get('enlace', '').strip()

            # COINCIDE CON TU HTML
            portada = request.FILES.get('imagen_portada')

            # Validaciones básicas
            if not titulo or not descripcion or not categoria_id:
                messages.error(request, 'Por favor completa todos los campos obligatorios (Título, Descripción, Categoría).')
                return redirect('miapp:pasante_gestion_recursos')
            
            if not url:
                messages.error(request, 'Debes proporcionar un ENLACE (URL).')
                return redirect('miapp:pasante_gestion_recursos')
            
            try:
                Recurso.objects.create(
                    titulo=titulo,
                    descripcion=descripcion,
                    tipo_recurso=tipo_recurso,
                    categoria_id=categoria_id,
                    contenido=contenido,
                    es_publico=es_publico,
                    url=url if url else None,
                    portada=portada if portada else None,
                    creado_por=request.user
                )
                messages.success(request, f'Recurso "{titulo}" creado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al crear recurso: {e}')
            
            return redirect('miapp:pasante_gestion_recursos')
        

        # ---------------------------------------------------------
        # EDITAR RECURSO  (CORREGIDO PARA COINCIDIR CON TU HTML)
        # ---------------------------------------------------------
        elif 'editar_recurso' in request.POST:

            recurso_id = request.POST.get('recurso_id')
            recurso = get_object_or_404(Recurso, id=recurso_id, creado_por=request.user)
            
            titulo = request.POST.get('titulo', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            tipo_recurso = request.POST.get('tipo_recurso')
            categoria_id = request.POST.get('categoria')
            contenido = request.POST.get('contenido', '').strip()
            es_publico = request.POST.get('es_publico') == 'on'

            # HTML usa "enlace", no "url"
            url = request.POST.get('enlace', '').strip()

            # HTML usa "imagen_portada", no "portada"
            nueva_portada = request.FILES.get('imagen_portada')

            if not titulo or not descripcion or not categoria_id:
                messages.error(request, 'Por favor completa todos los campos obligatorios (Título, Descripción, Categoría).')
                return redirect('miapp:pasante_gestion_recursos')
            
            if not url and not recurso.url:
                messages.error(request, 'El recurso debe tener un ENLACE (URL).')
                return redirect('miapp:pasante_gestion_recursos')
            
            try:
                recurso.titulo = titulo
                recurso.descripcion = descripcion
                recurso.tipo_recurso = tipo_recurso
                recurso.categoria_id = categoria_id
                recurso.contenido = contenido
                recurso.es_publico = es_publico
                recurso.url = url if url else None

                # Reemplazar portada si se sube una nueva
                if nueva_portada:
                    recurso.portada = nueva_portada
                
                recurso.save()
                messages.success(request, f'Recurso "{titulo}" actualizado correctamente')
            
            except Exception as e:
                messages.error(request, f'Error al actualizar recurso: {e}')
            
            return redirect('miapp:pasante_gestion_recursos')
        

        # ---------------------------------------------------------
        # ELIMINAR RECURSO
        # ---------------------------------------------------------
        elif 'eliminar_recurso' in request.POST:
            recurso_id = request.POST.get('recurso_id')
            recurso = get_object_or_404(Recurso, id=recurso_id, creado_por=request.user)
            titulo = recurso.titulo

            try:
                recurso.delete()
                messages.success(request, f'Recurso "{titulo}" eliminado')
            except Exception as e:
                messages.error(request, f'Error al eliminar recurso: {e}')
            
            return redirect('miapp:pasante_gestion_recursos')
    

    return render(request, 'miapp/pasante/gestion_recursos.html', {
        'recursos': recursos_list,
        'categorias': categorias
    })


@login_required
def pasante_consultas(request):
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.es_pasante():
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('miapp:index')
    
    consultas = FormularioContacto.objects.all().select_related('usuario')
    
    if request.method == 'POST':
        consulta_id = request.POST.get('consulta_id')
        respuesta = request.POST.get('respuesta')
        
        consulta = get_object_or_404(FormularioContacto, id=consulta_id)
        # Crear respuesta usando el nuevo modelo
        RespuestaConsulta.objects.create(
            consulta=consulta,
            respondido_por=request.user,
            respuesta=respuesta
        )
        consulta.respondido = True
        consulta.save()
        messages.success(request, 'Respuesta enviada exitosamente')
    
    return render(request, 'miapp/pasante/consultas.html', {'consultas': consultas})

# ==================== VISTAS FORO COMUNITARIO ====================

@login_required
def foro_comunitario(request):
    """Vista principal del foro comunitario"""
    if not CategoriaForo.objects.exists():
        categorias_default = [
            {'nombre': 'Experiencias Personales', 'color': '#6C63FF', 'orden': 1},
            {'nombre': 'Consejos y Estrategias', 'color': '#4CAF50', 'orden': 2},
            {'nombre': 'Apoyo Emocional', 'color': '#FF6B6B', 'orden': 3},
            {'nombre': 'Preguntas y Dudas', 'color': '#FFA726', 'orden': 4},
        ]
        for cat_data in categorias_default:
            CategoriaForo.objects.create(
                nombre=cat_data['nombre'],
                color=cat_data['color'],
                orden=cat_data['orden']
            )
    
    categorias = CategoriaForo.objects.filter(es_activa=True).order_by('orden')
    
    categoria_id = request.GET.get('categoria', '')
    orden = request.GET.get('orden', 'recientes')
    
    hilos = HiloForo.objects.select_related('categoria', 'creado_por', 'creado_por__userprofile')
    
    if 'aplicar_filtros' in request.GET:
        if categoria_id and categoria_id != 'todas':
            hilos = hilos.filter(categoria_id=categoria_id)
    
    if orden == 'populares':
        hilos = hilos.order_by('-votos_positivos', '-visitas', '-actualizado_en')
    elif orden == 'antiguos':
        hilos = hilos.order_by('creado_en')
    else:
        hilos = hilos.order_by('-creado_en')
    
    stats = {
        'total_hilos': HiloForo.objects.count(),
        'total_respuestas': RespuestaForo.objects.count(),
        'hilos_abiertos': HiloForo.objects.filter(estado='abierto').count(),
    }
    
    context = {
        'hilos': hilos,
        'categorias': categorias,
        'categoria_actual': categoria_id,
        'orden_actual': orden,
        'stats': stats,
    }
    
    return render(request, 'miapp/foro_comunitario.html', context)

@login_required
def crear_hilo(request):
    """Vista para crear un nuevo hilo"""
    categorias = CategoriaForo.objects.filter(es_activa=True).order_by('orden')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        categoria_id = request.POST.get('categoria')
        es_anonimo = request.POST.get('es_anonimo') == 'on'
        
        if titulo and contenido and categoria_id:
            hilo = HiloForo.objects.create(
                titulo=titulo,
                contenido=contenido,
                categoria_id=categoria_id,
                creado_por=request.user,
                es_anonimo=es_anonimo
            )
            messages.success(request, 'Tu hilo ha sido creado exitosamente.')
            return redirect('miapp:detalle_hilo', hilo_id=hilo.id)
        else:
            messages.error(request, 'Por favor completa todos los campos obligatorios.')
    
    context = {
        'categorias': categorias,
    }
    
    return render(request, 'miapp/crear_hilo.html', context)

@login_required
def editar_hilo(request, hilo_id):
    """Vista para editar un hilo existente"""
    hilo = get_object_or_404(HiloForo, id=hilo_id)
    
    if request.user != hilo.creado_por:
        messages.error(request, 'No tienes permisos para editar este hilo.')
        return redirect('miapp:detalle_hilo', hilo_id=hilo_id)
    
    categorias = CategoriaForo.objects.filter(es_activa=True).order_by('orden')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        categoria_id = request.POST.get('categoria')
        es_anonimo = request.POST.get('es_anonimo') == 'on'
        
        if titulo and contenido and categoria_id:
            hilo.titulo = titulo
            hilo.contenido = contenido
            hilo.categoria_id = categoria_id
            hilo.es_anonimo = es_anonimo
            hilo.save()
            
            messages.success(request, 'Tu hilo ha sido actualizado exitosamente.')
            return redirect('miapp:detalle_hilo', hilo_id=hilo.id)
        else:
            messages.error(request, 'Por favor completa todos los campos obligatorios.')
    
    context = {
        'hilo': hilo,
        'categorias': categorias,
    }
    
    return render(request, 'miapp/editar_hilo.html', context)

@login_required
def detalle_hilo(request, hilo_id):
    """Vista para ver un hilo específico y sus respuestas"""
    hilo = get_object_or_404(
        HiloForo.objects.select_related('categoria', 'creado_por', 'creado_por__userprofile'),
        id=hilo_id
    )
    
    hilo.visitas += 1
    hilo.save()
    
    respuestas = hilo.respuestas.select_related('creado_por', 'creado_por__userprofile').order_by('creado_en')
    
    if request.method == 'POST':
        contenido = request.POST.get('contenido_respuesta')
        es_anonimo = request.POST.get('es_anonimo') == 'on'
        
        if contenido:
            RespuestaForo.objects.create(
                hilo=hilo,
                contenido=contenido,
                creado_por=request.user,
                es_anonimo=es_anonimo
            )
            messages.success(request, 'Tu respuesta ha sido publicada exitosamente.')
            return redirect('miapp:detalle_hilo', hilo_id=hilo.id)
    
    context = {
        'hilo': hilo,
        'respuestas': respuestas,
    }
    
    return render(request, 'miapp/detalle_hilo.html', context)

@login_required
def eliminar_hilo(request, hilo_id):
    """Vista para eliminar un hilo (solo admin/pasante)"""
    hilo = get_object_or_404(HiloForo, id=hilo_id)
    
    puede_eliminar = (
        hasattr(request.user, 'userprofile') and 
        (request.user.userprofile.es_admin() or request.user.userprofile.es_pasante())
    )
    
    if not puede_eliminar:
        messages.error(request, 'No tienes permisos para eliminar hilos. Solo el staff puede eliminar hilos.')
        return redirect('miapp:detalle_hilo', hilo_id=hilo_id)
    
    if request.method == 'POST':
        titulo = hilo.titulo
        hilo.delete()
        messages.success(request, f'El hilo "{titulo}" ha sido eliminado exitosamente.')
        return redirect('miapp:foro_comunitario')
    
    context = {
        'hilo': hilo,
    }
    
    return render(request, 'miapp/eliminar_hilo.html', context)

@login_required
def mapa_recursos(request):
    """
    Vista para el mapa de recursos de emergencia y lugares tranquilos
    """
    return render(request, 'miapp/mapa_recursos.html')

def preguntas_frecuentes(request):
    """Vista para la página de preguntas frecuentes"""
    return render(request, 'miapp/preguntas_frecuentes.html')

#============================================================================
#============================================================================
# ==================== VISTAS PARA EL TEST PERSONALIZADO ====================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import (PreguntaTestPersonalizado, OpcionRespuestaPersonalizado, 
                    RespuestaTestPersonalizado, ResultadoTestPersonalizado, ContenidoPersonalizado)

@login_required
def realizar_test(request):
    """Vista para que los pacientes realicen el test"""
    print("🔍 DEBUG: Entrando a realizar_test")
    print(f"🔍 DEBUG: Método: {request.method}")
    print(f"🔍 DEBUG: Usuario: {request.user}")
    
    if request.method == 'POST':
        print("🔍 DEBUG: Procesando POST...")
        # Procesar respuestas
        puntaje_total = 0
        respuestas = []
        
        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                pregunta_id = key.replace('pregunta_', '')
                try:
                    pregunta = PreguntaTestPersonalizado.objects.get(id=pregunta_id)
                    opcion = OpcionRespuestaPersonalizado.objects.get(id=value)
                    puntaje_total += opcion.puntaje
                    
                    # Guardar respuesta
                    respuesta = RespuestaTestPersonalizado(
                        paciente=request.user,
                        pregunta=pregunta,
                        opcion_elegida=opcion
                    )
                    respuestas.append(respuesta)
                    
                except (PreguntaTestPersonalizado.DoesNotExist, OpcionRespuestaPersonalizado.DoesNotExist):
                    pass
        
        # Guardar todas las respuestas
        RespuestaTestPersonalizado.objects.bulk_create(respuestas)
        
        # Calcular diagnóstico
        diagnostico = calcular_diagnostico(puntaje_total)
        
        # Guardar resultado
        resultado = ResultadoTestPersonalizado(
            paciente=request.user,
            puntaje_total=puntaje_total,
            diagnostico=diagnostico
        )
        resultado.save()
        
        print(f"🔍 DEBUG: Test completado - Puntaje: {puntaje_total}")
        return redirect('miapp:resultado_test', resultado_id=resultado.id)  # ← ¡IMPORTANTE!
    
    else:
        print("🔍 DEBUG: Mostrando formulario GET")
        # Mostrar el test
        preguntas = PreguntaTestPersonalizado.objects.all().order_by('numero')
        print(f"🔍 DEBUG: Preguntas encontradas: {preguntas.count()}")
        
        return render(request, 'miapp/realizar_test.html', {
            'preguntas': preguntas,
            'seccion_actual': 'test'
        })

def calcular_diagnostico(puntaje_total):
    """Función para calcular el diagnóstico basado en el puntaje"""
    if puntaje_total <= 20:
        return "Bienestar emocional adecuado. Continúa con tus estrategias de afrontamiento positivas."
    elif puntaje_total <= 40:
        return "Leve malestar emocional. Podrías beneficiarte de estrategias adicionales de manejo del estrés."
    elif puntaje_total <= 60:
        return "Malestar emocional moderado. Recomendable buscar apoyo psicológico y practicar técnicas de relajación."
    else:
        return "Malestar emocional significativo. Es importante buscar ayuda profesional de psicología."

@login_required
def resultado_test(request, resultado_id):
    """Vista para mostrar el resultado del test"""
    resultado = get_object_or_404(ResultadoTestPersonalizado, id=resultado_id, paciente=request.user)
    return render(request, 'miapp/resultado_test.html', {
        'resultado': resultado,
        'seccion_actual': 'test'
    })

@login_required
def ver_resultados_pasante(request):
    """Vista para que los pasantes vean los resultados DETALLADOS de los pacientes"""
    print("🔍 DEBUG: Entrando a ver_resultados_pasante")
    print(f"🔍 DEBUG: Usuario: {request.user.username}")
    print(f"🔍 DEBUG: Es pasante: {request.user.userprofile.es_pasante()}")
    
    if not request.user.userprofile.es_pasante() and not request.user.userprofile.es_admin():
        print("🔍 DEBUG: Redirigiendo - no es pasante ni admin")
        return redirect('miapp:index')
    
    resultados = ResultadoTestPersonalizado.objects.all().order_by('-fecha_test')
    print(f"🔍 DEBUG: Resultados encontrados: {resultados.count()}")
    
    # Agregar respuestas detalladas a cada resultado
    resultados_detallados = []
    for resultado in resultados:
        respuestas = RespuestaTestPersonalizado.objects.filter(
            paciente=resultado.paciente
        ).select_related('pregunta', 'opcion_elegida')
        
        print(f"🔍 DEBUG: Resultado de {resultado.paciente.username} - {respuestas.count()} respuestas")
        
        resultados_detallados.append({
            'resultado': resultado,
            'respuestas': respuestas
        })
    
    print(f"🔍 DEBUG: Enviando {len(resultados_detallados)} resultados al template")
    
    return render(request, 'miapp/pasante/ver_resultados.html', {
        'resultados_detallados': resultados_detallados,
        'seccion_actual': 'resultados'
    })

@login_required
def subir_contenido_personalizado(request, paciente_id):
    """Vista para que los pasantes suban contenido personalizado"""
    if not request.user.userprofile.es_pasante() and not request.user.userprofile.es_admin():
        return redirect('miapp:index')  
    
    from django.contrib.auth.models import User
    paciente = get_object_or_404(User, id=paciente_id)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        tipo_contenido = request.POST.get('tipo_contenido')
        archivo = request.FILES.get('archivo')
        url = request.POST.get('url')
        
        contenido = ContenidoPersonalizado(
            pasante=request.user,
            paciente=paciente,
            titulo=titulo,
            descripcion=descripcion,
            tipo_contenido=tipo_contenido,
            archivo=archivo,
            url=url
        )
        contenido.save()
        
        return redirect('miapp:ver_contenido_personalizado')  
    
    
    return render(request, 'miapp/pasante/subir_contenido.html', {
        'paciente': paciente,
        'seccion_actual': 'contenido'
    })

@login_required
def ver_contenido_personalizado(request):
    """Vista para que los pacientes vean su contenido personalizado"""
    contenido = ContenidoPersonalizado.objects.filter(paciente=request.user).order_by('-fecha_creacion')
    return render(request, 'miapp/ver_contenido_personalizado.html', {
        'contenido': contenido,
        'seccion_actual': 'mi_contenido'
    })

def calcular_resumen_por_seccion(respuestas):
    """Calcula un resumen por sección del test"""
    resumen = {'A': 0, 'B': 0, 'C': 0}
    for respuesta in respuestas:
        seccion = respuesta.pregunta.seccion
        resumen[seccion] += respuesta.opcion_elegida.puntaje
    return resumen

# ==================== VISTAS PARA "VER COMO USUARIO" ====================

def ver_como_usuario(request):
    """Vista para que los pasantes vean el sitio como usuarios normales"""
    print("🔍 DEBUG: Activando modo 'Ver como Usuario'")
    
    # Verificar que sea pasante o admin
    if not hasattr(request.user, 'userprofile') or (
        not request.user.userprofile.es_pasante() and 
        not request.user.userprofile.es_admin()
    ):
        return redirect('miapp:index')
    
    # Guardar en sesión que está en modo "ver como usuario"
    request.session['viewing_as_user'] = True
    request.session['original_user_type'] = request.user.userprofile.tipo_usuario
    print(f"🔍 DEBUG: Usuario {request.user.username} entrando en modo usuario")
    
    return redirect('miapp:index')

def volver_a_pasante(request):
    """Volver al modo pasante"""
    print("🔍 DEBUG: Volviendo al modo pasante")
    
    if 'viewing_as_user' in request.session:
        del request.session['viewing_as_user']
    if 'original_user_type' in request.session:
        del request.session['original_user_type']
    
    print(f"🔍 DEBUG: Usuario {request.user.username} volviendo a modo pasante")
    return redirect('miapp:pasante_dashboard')


@login_required
def recursos(request):
    """Vista para los recursos - Versión mejorada"""
    try:
        recursos_list = Recurso.objects.filter(es_publico=True)
        return render(request, 'miapp/recursos.html', {'recursos': recursos_list})
    except Exception as e:
        print(f"🔍 ERROR en vista recursos: {e}")
        # Si hay error, redirigir a una página segura
        return redirect('miapp:index')
