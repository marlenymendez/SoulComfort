from django.urls import path
from . import views

app_name = 'miapp'

urlpatterns = [
    # ==================== AUTENTICACIÓN ====================
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # ==================== PÁGINAS PÚBLICAS ====================
    path('', views.index, name='index'),  # Esta es tu página principal
    
    # ==================== PÁGINAS PARA USUARIOS AUTENTICADOS ====================
    path('datos-curiosos/', views.datos_curiosos, name='datos_curiosos'),
    path('recursos/', views.recursos, name='recursos'),
    path('recursos-multimedia/', views.recursos_multimedia, name='recursos_multimedia'),
    path('tests/', views.tests_psicologicos, name='tests'),
    path('contacto/', views.formulario_contacto, name='formulario_contacto'),
    
    # ==================== PERFIL DE USUARIO ====================
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    
    # ==================== DASHBOARDS ESPECÍFICOS ====================
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('pasante/dashboard/', views.pasante_dashboard, name='pasante_dashboard'),

   # URLs DEL FORO COMUNITARIO ACTUALIZADAS
    path('foro/', views.foro_comunitario, name='foro_comunitario'),
    path('foro/crear/', views.crear_hilo, name='crear_hilo'),
    path('foro/hilo/<int:hilo_id>/', views.detalle_hilo, name='detalle_hilo'),
    path('foro/hilo/<int:hilo_id>/editar/', views.editar_hilo, name='editar_hilo'),
    path('foro/hilo/<int:hilo_id>/eliminar/', views.eliminar_hilo, name='eliminar_hilo'),
    
    # ==================== ADMINISTRACIÓN (SOLO ADMIN) ====================
    path('admin/usuarios/', views.admin_gestion_usuarios, name='admin_gestion_usuarios'),
    path('admin/recursos/', views.admin_gestion_recursos, name='admin_gestion_recursos'),
    path('admin/consultas/', views.admin_consultas, name='admin_consultas'),
    
    # ==================== PASANTE (SOLO PASANTE) ====================
    path('pasante/recursos/', views.pasante_gestion_recursos, name='pasante_gestion_recursos'),
    path('pasante/consultas/', views.pasante_consultas, name='pasante_consultas'),

    #======================MAPAAAAAA===============================
    path('mapa-recursos/', views.mapa_recursos, name='mapa_recursos'),

      # ==================== PREGUNTAS FRECUENTES ====================
    path('preguntas-frecuentes/', views.preguntas_frecuentes, name='preguntas_frecuentes'),

    
    # ==================== URLs para el Test Personalizado ===========
    path('realizar-test/', views.realizar_test, name='realizar_test'),
    path('resultado-test/<int:resultado_id>/', views.resultado_test, name='resultado_test'),
    path('ver-resultados/', views.ver_resultados_pasante, name='ver_resultados_pasante'),
    path('subir-contenido/<int:paciente_id>/', views.subir_contenido_personalizado, name='subir_contenido_personalizado'),
    path('mi-contenido/', views.ver_contenido_personalizado, name='ver_contenido_personalizado'),

    # ===================== VER COMO USUARIO =====================
    path('ver-como-usuario/', views.ver_como_usuario, name='ver_como_usuario'),
    path('volver-a-pasante/', views.volver_a_pasante, name='volver_a_pasante'), 
]

