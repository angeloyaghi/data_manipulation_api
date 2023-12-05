docker build -t first_image_manipulation .
docker run -v /home/anthony/output_isaac:/my_data -itd -p 80:80 --name data_manipulation first_image_manipulation
/my_data/randomization_2023-08-07-11-33-14