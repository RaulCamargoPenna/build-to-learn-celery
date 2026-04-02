# Objetivo:
Estudar uma estrutura específica de projeto usando UV e destrinchando as configurações do celery afim de conseguir realizar operações via api.

## Dependências utilizadas:
- celery==5.6
- django==5.1
- django-celery-beat>=2.9.0
- django-celery-results>=2.6.0

## Problema:
Atualmente trabalho em um projeto interno da empresa que foi o primeiro projeto que criei. Comecei a enfrentar problemas com tarefas assíncronas e algumas limitações que foram causadas pela minha própria implemetação.

- Essa primeira implementação não estava errada, porém acabou deixando essa parte de tarefas assíncronas limitada, por exemplo: Em um cenário onde uma nova task era criada, eu precisava fazer o registro dela no arquivo celery.py e depois reiniciar os workers.

- Outro problema que encontrei foi que eu usava dois Wokers diferentes e cada um escutava uma fila específica usando o argumento `--pool=solo` o que faz rodar sem paralelismo, estudando mais sobre o assunto eu entendi que isso fazia cada **worker** processar apenas uma task por vez no processo dele.

- Uma outra abordagem que eu acabei mudando foi a de como exibir, salvar e gerenciar os resultados das tarefas que foram executadas. Antes eu estava utilizando `redis` como broker + `flower` para vizualização e agora passei a utilizar o `RabbitMQ` + `BD`.

## RabbitMQ:
Como eu estou usando Windows optei por usar o WSL para iniciar o serviço do `RabbitMQ`.
- WSL: https://learn.microsoft.com/en-us/windows/wsl/install
- RabbitMQ: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html#broker-rabbitmq

# Soluções:

## Criação de novas tasks:
Quando uma nova tarefa é criada ainda é necessário subir a atualização que contém ela para o servidor, porém com os endpoints disponíveis no app `tasks` conseguimos configurar a execução de uma task via API.

## Consumo desnecessário de threads:
Conforme dito anteriormente, antes eu tinha 2 workers com `--pool=solo`, onde cada um processava apenas 1 task, ou seja, sem paralelismo. Agora subo apenas um **worker** com `--pool=threads` que instrui o Celery a criar threads dentro do mesmo processo, e `--concurrency=N` onde **N** define quantas threads podem processar tarefas simultaneamente. Outro argumento passado ao iniciar o worker é o `-Q` seguido dos nomes das filas que ele deve escutar, ex: `-Q fila_1,fila_2`

## RabbitMQ vs Redis:
Escolhi migrar para o `RabbitMQ` pois achei a ferramenta mais escalável, subir o serviço é simples e a você consegue gerenciar (purge) as filas de maneira mais simples apenas dando permissão para o usuário desejado. Além disso o `RabbitMQ` mantém as mensagens por padrão.

### Registros de resultados:
Antes eu utilizava o `flower` que da maneira que estava configurado junto ao `redis` estava com algumas limitações e caso eu reiniciasse o serviço eu perdia todos os registros. Isso foi alterado e agora são utilizadas as próprias tabelas da que o `django_celery_results` cria persistindo os registros no banco de dados e não mais em memória como era com o `redis`.