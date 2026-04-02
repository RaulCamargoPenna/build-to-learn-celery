from django.urls import path
from . import views

urlpatterns = [
    path("registrar/", views.registrar_task,  name="registrar_task"),
    path("listar/", views.listar_tasks,    name="listar_tasks"),
    path("<int:task_id>/remover/",  views.remover_task,  name="remover_task"),
    path("cancelar/", views.cancelar_task, name="cancelar_task"),
    path("ativas/", views.listar_tasks_ativas, name="listar_tasks_ativas"),
]