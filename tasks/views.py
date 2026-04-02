import json
import zoneinfo
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from celery.app.control import Control
from app.celery import app as celery_app


# ------------------------------------------------------------------
# POST /tasks/registrar/
# Body: {"nome": "...", "task": "tasks.tasks.tarefa_rapida",
#        "tipo": "crontab|intervalo",
#        "crontab": {"minute": "*/5", "hour": "*", ...},   # se tipo=crontab
#        "intervalo": {"every": 10, "period": "seconds"},  # se tipo=intervalo
#        "args": [], "kwargs": {}, "fila": "default"}
# ------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def registrar_task(request):
    try:
        data = json.loads(request.body)

        nome  = data.get("nome")
        task  = data.get("task")
        tipo  = data.get("tipo", "crontab")
        fila  = data.get("fila", "default")
        args  = json.dumps(data.get("args", []))
        kwargs = json.dumps(data.get("kwargs", {}))
        tz    = zoneinfo.ZoneInfo("America/Sao_Paulo")

        if not nome or not task:
            return JsonResponse({"erro": "nome e task são obrigatórios"}, status=400)

        if tipo == "crontab":
            c = data.get("crontab", {})
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=c.get("minute", "*"),
                hour=c.get("hour", "*"),
                day_of_week=c.get("day_of_week", "*"),
                day_of_month=c.get("day_of_month", "*"),
                month_of_year=c.get("month_of_year", "*"),
                timezone=tz,
            )
            pt = PeriodicTask.objects.create(
                name=nome, task=task,
                crontab=schedule,
                args=args, kwargs=kwargs,
                queue=fila,
            )

        elif tipo == "intervalo":
            i = data.get("intervalo", {})
            period_map = {
                "seconds": IntervalSchedule.SECONDS,
                "minutes": IntervalSchedule.MINUTES,
                "hours":   IntervalSchedule.HOURS,
                "days":    IntervalSchedule.DAYS,
            }
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=i.get("every", 10),
                period=period_map.get(i.get("period", "seconds"), IntervalSchedule.SECONDS),
            )
            pt = PeriodicTask.objects.create(
                name=nome, task=task,
                interval=schedule,
                args=args, kwargs=kwargs,
                queue=fila,
            )
        else:
            return JsonResponse({"erro": "tipo inválido, use 'crontab' ou 'intervalo'"}, status=400)

        return JsonResponse({"id": pt.id, "nome": pt.name, "status": "criada"}, status=201)

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)


# ------------------------------------------------------------------
# GET  /tasks/listar/
# ------------------------------------------------------------------
def listar_tasks(request):
    tasks = PeriodicTask.objects.values(
        "id", "name", "task", "enabled",
        "queue", "last_run_at", "total_run_count"
    )
    return JsonResponse({"tasks": list(tasks)})


# ------------------------------------------------------------------
# POST /tasks/<id>/cancelar/
# Cancela uma execução em andamento (revoke + terminate)
# ------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def cancelar_task(request):
    try:
        data = json.loads(request.body) if request.body else {}
        celery_task_id = data.get("id")  # ID retornado pelo .delay()

        if not celery_task_id:
            return JsonResponse({"erro": "celery_task_id é obrigatório"}, status=400)

        celery_app.control.revoke(celery_task_id, terminate=True, signal="SIGTERM")
        return JsonResponse({"status": "revoke enviado", "celery_task_id": celery_task_id})

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)


# ------------------------------------------------------------------
# DELETE /tasks/<id>/remover/
# Remove o agendamento da task do banco
# ------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["DELETE"])
def remover_task(request, task_id):
    try:
        pt = PeriodicTask.objects.get(id=task_id)
        pt.delete()
        return JsonResponse({"status": "removida", "id": task_id})
    except PeriodicTask.DoesNotExist:
        return JsonResponse({"erro": "task não encontrada"}, status=404)
    

# GET /tasks/ativas/
def listar_tasks_ativas(request):
    inspect = celery_app.control.inspect()
    
    ativas = inspect.active()   # tasks em execução agora
    reservadas = inspect.reserved()  # tasks recebidas mas ainda não iniciadas
    
    return JsonResponse({
        "ativas": ativas or {},
        "reservadas": reservadas or {},
    })