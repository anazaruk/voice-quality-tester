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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nisqa_carriers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `carrier_name` varchar(128) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_carrier_name` (`carrier_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nisqa_carrier_ips` (
  `id` int NOT NULL AUTO_INCREMENT,
  `carrier_id` int NOT NULL,
  `ip_address` varchar(64) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_carrier_ip_address` (`ip_address`),
  KEY `idx_carrier_ip_lookup` (`ip_address`),
  KEY `idx_carrier_ips_carrier` (`carrier_id`),
  CONSTRAINT `fk_carrier_ips_carrier` FOREIGN KEY (`carrier_id`) REFERENCES `nisqa_carriers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
