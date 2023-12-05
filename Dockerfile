# ALWAYS USE THIS ARCHITECTURE OF DOCKERFILE FOR FASTER AND BETTER BUILD TIME
# 
FROM python:3.9

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# --no-cache-dir means dont install locally
# --upgrade means upgrade the packages if they are already installed
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY . /code

# list of string which is what you would type in the command line seperated by spaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]