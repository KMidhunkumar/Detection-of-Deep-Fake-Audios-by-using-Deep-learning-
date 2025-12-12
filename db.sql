drop database if exists deep_fake;
create database deep_fake;
use deep_fake;


create table users(id INT PRIMARY KEY AUTO_INCREMENT, email VARCHAR(50), password VARCHAR(50));