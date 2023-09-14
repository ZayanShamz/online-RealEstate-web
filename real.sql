/*
SQLyog Community v13.2.0 (64 bit)
MySQL - 5.1.32-community : Database - realestate
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`realestate` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `realestate`;

/*Table structure for table `dealer` */

DROP TABLE IF EXISTS `dealer`;

CREATE TABLE `dealer` (
  `dealer_id` int(11) NOT NULL AUTO_INCREMENT,
  `login_id` int(11) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(100) DEFAULT NULL,
  `gender` varchar(50) DEFAULT NULL,
  `dob` varchar(100) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`dealer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

/*Data for the table `dealer` */

insert  into `dealer`(`dealer_id`,`login_id`,`name`,`email`,`phone`,`gender`,`dob`,`password`) values 
(1,3,'dealer1','d1','787987896','male','1989-08-12','d1');

/*Table structure for table `engineer` */

DROP TABLE IF EXISTS `engineer`;

CREATE TABLE `engineer` (
  `eng_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `exp` int(11) DEFAULT NULL,
  `discipline` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `dob` varchar(20) DEFAULT NULL,
  `place` varchar(500) DEFAULT NULL,
  `filename` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`eng_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

/*Data for the table `engineer` */

/*Table structure for table `login` */

DROP TABLE IF EXISTS `login`;

CREATE TABLE `login` (
  `lid` int(30) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) DEFAULT NULL,
  `password` varchar(30) DEFAULT NULL,
  `usertype` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`lid`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

/*Data for the table `login` */

insert  into `login`(`lid`,`username`,`password`,`usertype`) values 
(1,'admin','admin','admin'),
(3,'d1','d1','user');

/*Table structure for table `merchant` */

DROP TABLE IF EXISTS `merchant`;

CREATE TABLE `merchant` (
  `merc_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `dob` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `bname` varchar(100) DEFAULT NULL,
  `btype` varchar(50) DEFAULT NULL,
  `location` varchar(500) DEFAULT NULL,
  `filename` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`merc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

/*Data for the table `merchant` */

/*Table structure for table `plot` */

DROP TABLE IF EXISTS `plot`;

CREATE TABLE `plot` (
  `plot_id` int(11) NOT NULL AUTO_INCREMENT,
  `login_id` int(11) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `address` varchar(300) DEFAULT NULL,
  `area` varchar(100) DEFAULT NULL,
  `type` varchar(100) DEFAULT NULL,
  `price` varchar(30) DEFAULT NULL,
  `filename` varchar(100) DEFAULT NULL,
  `ext` varchar(50) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `requests` varchar(11) DEFAULT NULL,
  PRIMARY KEY (`plot_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

/*Data for the table `plot` */

insert  into `plot`(`plot_id`,`login_id`,`name`,`address`,`area`,`type`,`price`,`filename`,`ext`,`count`,`status`,`requests`) values 
(1,3,'d1 plot 1','Yatheem Khana Juma Masjid, Chemmad - Kakkad Road, Tirurangadi, Malappuram District, Kerala, 676306, India','32390','land','720000','dealer1(3)_d1 plot 1','.jpg',3,'pending','0');

/*Table structure for table `plot_images` */

DROP TABLE IF EXISTS `plot_images`;

CREATE TABLE `plot_images` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_id` int(11) DEFAULT NULL,
  `filename` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

/*Data for the table `plot_images` */

insert  into `plot_images`(`id`,`ref_id`,`filename`) values 
(1,1,'dealer1(3)_d1 plot 1-1.jpg'),
(2,1,'dealer1(3)_d1 plot 1-2.jpg'),
(3,1,'dealer1(3)_d1 plot 1-3.jpg');

/*Table structure for table `plot_locations` */

DROP TABLE IF EXISTS `plot_locations`;

CREATE TABLE `plot_locations` (
  `loc_id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_id` int(11) DEFAULT NULL,
  `latitude` varchar(100) DEFAULT NULL,
  `longitude` varchar(100) DEFAULT NULL,
  `address` varchar(300) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `county` varchar(100) DEFAULT NULL,
  `zipcode` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`loc_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

/*Data for the table `plot_locations` */

insert  into `plot_locations`(`loc_id`,`ref_id`,`latitude`,`longitude`,`address`,`state`,`county`,`zipcode`) values 
(1,1,'11.041715950844468','75.9309929464092','Yatheem Khana Juma Masjid, Chemmad - Kakkad Road, Tirurangadi, Malappuram District, Kerala, 676306, India','Kerala','Tirurangadi','676306');

/*Table structure for table `plot_requests` */

DROP TABLE IF EXISTS `plot_requests`;

CREATE TABLE `plot_requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pid` int(11) DEFAULT NULL,
  `dealer_id` int(11) DEFAULT NULL,
  `date` varchar(20) DEFAULT NULL,
  `time` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

/*Data for the table `plot_requests` */

/*Table structure for table `rental` */

DROP TABLE IF EXISTS `rental`;

CREATE TABLE `rental` (
  `rental_id` int(30) NOT NULL AUTO_INCREMENT,
  `login_id` int(11) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `address` varchar(500) DEFAULT NULL,
  `area` varchar(100) DEFAULT NULL,
  `rent` varchar(15) DEFAULT NULL,
  `storey` varchar(100) DEFAULT NULL,
  `filename` varchar(100) DEFAULT NULL,
  `ext` varchar(50) DEFAULT NULL,
  `count` int(11) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `requests` varchar(11) DEFAULT NULL,
  PRIMARY KEY (`rental_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

/*Data for the table `rental` */

insert  into `rental`(`rental_id`,`login_id`,`name`,`address`,`area`,`rent`,`storey`,`filename`,`ext`,`count`,`status`,`requests`) values 
(1,3,'d1 rentals 1','KSEB TGI, Chemmad Bypass Road, Chemmad, Chandappadi, Tirurangadi, Malappuram District, Kerala, 676306, India','7821','240000','Multi Storey Multi Rooms','dealer1(3)_d1 rentals 1','.jpg',3,'pending','0');

/*Table structure for table `rental_images` */

DROP TABLE IF EXISTS `rental_images`;

CREATE TABLE `rental_images` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_id` int(11) DEFAULT NULL,
  `filename` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

/*Data for the table `rental_images` */

insert  into `rental_images`(`id`,`ref_id`,`filename`) values 
(1,1,'dealer1(3)_d1 rentals 1-1.jpg'),
(2,1,'dealer1(3)_d1 rentals 1-2.jpg'),
(3,1,'dealer1(3)_d1 rentals 1-3.jpg');

/*Table structure for table `rental_locations` */

DROP TABLE IF EXISTS `rental_locations`;

CREATE TABLE `rental_locations` (
  `loc_id` int(11) NOT NULL AUTO_INCREMENT,
  `ref_id` int(11) DEFAULT NULL,
  `latitude` varchar(100) DEFAULT NULL,
  `longitude` varchar(100) DEFAULT NULL,
  `address` varchar(300) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `county` varchar(100) DEFAULT NULL,
  `zipcode` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`loc_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

/*Data for the table `rental_locations` */

insert  into `rental_locations`(`loc_id`,`ref_id`,`latitude`,`longitude`,`address`,`state`,`county`,`zipcode`) values 
(1,1,'11.043742943552665','75.92300584462697','KSEB TGI, Chemmad Bypass Road, Chemmad, Chandappadi, Tirurangadi, Malappuram District, Kerala, 676306, India','Kerala','Tirurangadi','676306');

/*Table structure for table `rental_requests` */

DROP TABLE IF EXISTS `rental_requests`;

CREATE TABLE `rental_requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `rid` int(11) DEFAULT NULL,
  `dealer_id` int(11) DEFAULT NULL,
  `date` varchar(20) DEFAULT NULL,
  `time` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

/*Data for the table `rental_requests` */

/*Table structure for table `sales` */

DROP TABLE IF EXISTS `sales`;

CREATE TABLE `sales` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pid` int(11) DEFAULT NULL,
  `buyer` int(11) DEFAULT NULL,
  `date` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

/*Data for the table `sales` */

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
