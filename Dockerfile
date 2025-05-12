FROM continuumio/miniconda3:latest

LABEL main='for-documents'

WORKDIR /app

COPY . /app

RUN conda env create -f /app/telegrambot.yml  \
    && echo "conda activate tgBots" > ~/.bashrc  \
    && conda clean -afy

ENV PATH="/opt/conda/envs/tgBots/bin:$PATH"

EXPOSE 5432

CMD ["python", "run.py"]
