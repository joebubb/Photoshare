CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;

DROP TABLE IF EXISTS Likes;
DROP TABLE IF EXISTS Tags;
DROP TABLE IF EXISTS Pictures;
DROP TABLE IF EXISTS Comments;
DROP TABLE IF EXISTS Albums;
DROP TABLE IF EXISTS Friends;
DROP TABLE IF EXISTS Users;

CREATE TABLE Users (
    email varchar(255) UNIQUE,
    password varchar(255),
    first_name varchar(50),
    last_name varchar(50),
    user_id int4  AUTO_INCREMENT,
    date_of_birth DATE,
    hometown varchar(255) ,
    gender varchar(50),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends 
(
	friend_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    PRIMARY KEY(friend_id, user_id), 
    FOREIGN KEY(friend_id) REFERENCES Users(user_id), 
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
);

CREATE TABLE Albums
(
	albumID int4 auto_increment, 
    userID int4, 
    name varchar(255), 
    dateCreated date, 
    primary key (albumID),
    foreign key (userID) references Users (user_id)
);

CREATE TABLE Comments
(
	user_id INTEGER,
    photo_id INTEGER,
    comment varchar(500),
    comment_id int4  AUTO_INCREMENT,
    PRIMARY KEY(comment_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  album int4,
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (album) REFERENCES Albums(albumID)
);

CREATE TABLE Tags
(
	tagID int4 auto_increment,
	tagname varchar(255),
    photo int4,
    primary key (tagID),
    foreign key (photo) references Pictures (picture_id)
);

CREATE TABLE Likes
(
	user_id int4, 
    photo_id int4,
    primary key (user_id, photo_id),
    foreign key (user_id) references Users (user_id),
    foreign key (photo_id) references Pictures (picture_id)
);

INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
