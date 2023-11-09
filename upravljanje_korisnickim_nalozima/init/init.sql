create database users;
use users;

create table user (
    id int primary key AUTO_INCREMENT,
    email varchar(256) not null unique,
    password varchar(256) not null,
    forename varchar(256) not null,
    surname varchar(256) not null,
    role varchar(256) not null
);

insert into user values (1, "onlymoney@gmail.com", "evenmoremoney", "Scrooge", "McDuck", "owner");
