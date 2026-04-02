from celery import shared_task
import time

@shared_task(bind=True)
def tarefa_rapida(self, mensagem=""):
    print(f"[tarefa_rapida] executando: {mensagem}")
    return {"status": "ok", "mensagem": mensagem}

@shared_task(bind=True)
def tarefa_demorada(self, segundos=10):
    print(f"[tarefa_demorada] iniciando, vai demorar {segundos}s")
    time.sleep(segundos)
    return {"status": "ok", "durou": segundos}