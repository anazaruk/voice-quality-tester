-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: voice_quality
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `nisqa_cdr`
--

DROP TABLE IF EXISTS `nisqa_cdr`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nisqa_cdr` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `uniqueid` varchar(64) DEFAULT NULL,
  `source_ip` varchar(64) DEFAULT NULL,
  `source_ip_country` varchar(128) DEFAULT NULL,
  `source_ip_asn` varchar(32) DEFAULT NULL,
  `source_ip_carrier` varchar(255) DEFAULT NULL,
  `source_number` varchar(64) DEFAULT NULL,
  `source_state` varchar(128) DEFAULT NULL,
  `source_region` varchar(16) DEFAULT NULL,
  `source_timezone` varchar(128) DEFAULT NULL,
  `destination_number` varchar(64) DEFAULT NULL,
  `destination_state` varchar(128) DEFAULT NULL,
  `destination_region` varchar(16) DEFAULT NULL,
  `duration` int DEFAULT NULL,
  `recording_file` varchar(255) DEFAULT NULL,
  `codec` varchar(32) DEFAULT NULL,
  `mos_pred` float DEFAULT NULL,
  `noi_pred` float DEFAULT NULL,
  `dis_pred` float DEFAULT NULL,
  `col_pred` float DEFAULT NULL,
  `loud_pred` float DEFAULT NULL,
  `transcript` text,
  `reference_text` text,
  `word_error_rate` float DEFAULT NULL,
  `rtp_avg_rx_loss` float DEFAULT NULL,
  `rtp_avg_tx_loss` float DEFAULT NULL,
  `rtp_avg_rx_jitter` float DEFAULT NULL,
  `rtp_avg_tx_jitter` float DEFAULT NULL,
  `rtp_avg_rtt` float DEFAULT NULL,
  `status` varchar(32) DEFAULT NULL,
  `trailing_silence_sec` decimal(6,2) DEFAULT '0.00',
  `total_silence_sec` decimal(6,2) DEFAULT '0.00',
  `speech_duration_sec` decimal(6,2) DEFAULT '0.00',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=501969 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nisqa_dialer_targets`
--

DROP TABLE IF EXISTS `nisqa_dialer_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nisqa_dialer_targets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `caller_id` varchar(32) NOT NULL,
  `dst_number` varchar(32) NOT NULL,
  `trunk_name` varchar(128) NOT NULL,
  `audio_file` varchar(255) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `last_called_at` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'voice_quality'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-21 15:30:20
