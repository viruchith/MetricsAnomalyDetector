#!/usr/bin/env python3
"""
Clean Reactive Dashboard for Predictive Maintenance System
Real-time monitoring with Lumen branding and team credits
"""

from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit
import pandas as pd
import json
import os
from datetime import datetime
import joblib
import numpy as np
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumen_predictive_maintenance'
socketio = SocketIO(app, cors_allowed_origins="*")

# Clean Dashboard HTML Template
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 Lumen Predictive Maintenance Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #34495e 100%);
            background-attachment: fixed;
            color: #2c3e50;
            overflow-x: hidden;
            min-height: 100vh;
        }
        
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #34495e 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .live-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(52, 73, 94, 0.9);
            backdrop-filter: blur(10px);
            padding: 15px 25px;
            border-radius: 50px;
            color: #ecf0f1;
            font-weight: 700;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(236, 240, 241, 0.2);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .live-dot {
            width: 12px;
            height: 12px;
            background: #27ae60;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 30px 50px;
            background: rgba(52, 73, 94, 0.9);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(189, 195, 199, 0.3);
            margin-bottom: 30px;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 30px;
        }
        
        .lumen-logo {
            font-size: 3em;
            font-weight: 800;
            color: #3498db;
            text-shadow: 0 0 20px rgba(52, 152, 219, 0.3);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .lumen-logo:hover {
            transform: scale(1.1);
            text-shadow: 0 0 30px rgba(52, 152, 219, 0.5);
        }
        
        .title-section h1 {
            font-size: 2.5em;
            font-weight: 700;
            color: #ecf0f1;
            margin-bottom: 10px;
        }
        
        .title-section p {
            font-size: 1.3em;
            color: #bdc3c7;
            font-weight: 500;
        }
        
        .team-credits {
            text-align: right;
            color: #ecf0f1;
        }
        
        .team-credits h3 {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #3498db;
        }
        
        .team-member {
            font-size: 1.1em;
            margin: 8px 0;
            padding: 8px 15px;
            background: rgba(52, 152, 219, 0.2);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(52, 152, 219, 0.3);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 30px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(236, 240, 241, 0.95);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            border: 1px solid rgba(189, 195, 199, 0.3);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card:hover {
            transform: translateY(-10px) scale(1.05);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .stat-icon {
            font-size: 3em;
            margin-bottom: 15px;
            display: block;
        }
        
        .stat-icon.info { color: #2980b9; }
        .stat-icon.critical { color: #e74c3c; }
        .stat-icon.warning { color: #f39c12; }
        .stat-icon.normal { color: #27ae60; }
        
        .stat-value {
            font-size: 3em;
            font-weight: 800;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .stat-value.critical { color: #c0392b; }
        .stat-value.warning { color: #d68910; }
        .stat-value.normal { color: #27ae60; }
        .stat-value.info { color: #2980b9; }
        
        .stat-label {
            font-size: 1.2em;
            color: #5d6d7e;
            font-weight: 600;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .chart-card {
            background: rgba(236, 240, 241, 0.95);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid rgba(189, 195, 199, 0.3);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        }
        
        .chart-title {
            font-size: 1.5em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .chart-container {
            height: 300px;
        }
        
        .machines-section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 2em;
            font-weight: 700;
            color: #ecf0f1;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .machine-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(248, 249, 250, 0.9));
            backdrop-filter: blur(20px);
            margin-bottom: 25px;
            padding: 30px;
            border-radius: 20px;
            border: 2px solid transparent;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15), 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }
        
        .machine-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3498db, #2980b9);
            transition: all 0.4s ease;
        }
        
        .machine-card.high-risk {
            border: 2px solid rgba(231, 76, 60, 0.3);
            background: linear-gradient(145deg, rgba(255, 235, 238, 0.95), rgba(254, 242, 242, 0.9));
            box-shadow: 0 15px 40px rgba(231, 76, 60, 0.2), 0 5px 15px rgba(231, 76, 60, 0.1);
        }
        
        .machine-card.high-risk::before {
            background: linear-gradient(90deg, #e74c3c, #c0392b, #ff6b6b);
            height: 6px;
        }
        
        .machine-card.medium-risk {
            border: 2px solid rgba(243, 156, 18, 0.3);
            background: linear-gradient(145deg, rgba(255, 249, 235, 0.95), rgba(254, 252, 242, 0.9));
            box-shadow: 0 15px 40px rgba(243, 156, 18, 0.2), 0 5px 15px rgba(243, 156, 18, 0.1);
        }
        
        .machine-card.medium-risk::before {
            background: linear-gradient(90deg, #f39c12, #e67e22, #ff9f43);
            height: 5px;
        }
        
        .machine-card.low-risk {
            border: 2px solid rgba(39, 174, 96, 0.3);
            background: linear-gradient(145deg, rgba(236, 253, 243, 0.95), rgba(242, 255, 249, 0.9));
            box-shadow: 0 15px 40px rgba(39, 174, 96, 0.2), 0 5px 15px rgba(39, 174, 96, 0.1);
        }
        
        .machine-card.low-risk::before {
            background: linear-gradient(90deg, #2ecc71, #27ae60, #00d2d3);
            height: 4px;
        }
        
        .machine-card:hover {
            transform: translateY(-8px) scale(1.03);
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.25), 0 10px 25px rgba(0, 0, 0, 0.15);
        }
        
        .machine-card.high-risk:hover {
            box-shadow: 0 25px 60px rgba(231, 76, 60, 0.35), 0 10px 25px rgba(231, 76, 60, 0.2);
        }
        
        .machine-card.medium-risk:hover {
            box-shadow: 0 25px 60px rgba(243, 156, 18, 0.35), 0 10px 25px rgba(243, 156, 18, 0.2);
        }
        
        .machine-card.low-risk:hover {
            box-shadow: 0 25px 60px rgba(39, 174, 96, 0.35), 0 10px 25px rgba(39, 174, 96, 0.2);
        }
        
        .machine-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            position: relative;
        }
        
        .machine-id {
            font-size: 1.8em;
            font-weight: 800;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 15px;
            position: relative;
        }
        
        .machine-id::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 0;
            height: 3px;
            background: linear-gradient(90deg, #3498db, #2980b9);
            transition: width 0.4s ease;
        }
        
        .machine-card:hover .machine-id::after {
            width: 100%;
        }
        
        .machine-icon {
            font-size: 2.2em;
            padding: 15px;
            border-radius: 15px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .machine-card.high-risk .machine-icon {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
        }
        
        .machine-card.medium-risk .machine-icon {
            background: linear-gradient(135deg, #f39c12, #e67e22);
            box-shadow: 0 8px 25px rgba(243, 156, 18, 0.4);
        }
        
        .machine-card.low-risk .machine-icon {
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        
        .risk-badge {
            padding: 12px 25px;
            border-radius: 30px;
            color: white;
            font-weight: 800;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            animation: pulse-glow 2s ease-in-out infinite;
        }
        
        .risk-badge::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: left 0.5s;
        }
        
        .risk-badge:hover::before {
            left: 100%;
        }
        
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2); }
            50% { box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3); }
        }
        
        .risk-high { 
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 50%, #a93226 100%);
            box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
        }
        .risk-medium { 
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 50%, #d68910 100%);
            box-shadow: 0 8px 25px rgba(243, 156, 18, 0.4);
        }
        .risk-low { 
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 50%, #229954 100%);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        
        .machine-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-top: 25px;
            margin-bottom: 20px;
        }
        
        .detail-item {
            text-align: center;
            padding: 20px;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.8), rgba(248, 249, 250, 0.6));
            border-radius: 15px;
            border: 2px solid rgba(52, 152, 219, 0.1);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .detail-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #3498db, #2980b9);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        
        .detail-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
            border-color: rgba(52, 152, 219, 0.3);
        }
        
        .detail-item:hover::before {
            transform: scaleX(1);
        }
        
        .detail-value {
            font-weight: 800;
            font-size: 1.4em;
            margin-bottom: 8px;
            color: #2c3e50;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .detail-label {
            font-size: 0.95em;
            color: #5d6d7e;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        
        .detail-icon {
            font-size: 1.2em;
            opacity: 0.8;
        }
        
        .issues-section {
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(145deg, rgba(52, 73, 94, 0.08), rgba(44, 62, 80, 0.05));
            border-radius: 15px;
            color: #2c3e50;
            border: 1px solid rgba(52, 152, 219, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .issues-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #e74c3c, #f39c12, #2ecc71);
            border-radius: 0 2px 2px 0;
        }
        
        .issues-title {
            font-weight: 800;
            font-size: 1.1em;
            margin-bottom: 10px;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .issues-content {
            font-size: 1em;
            line-height: 1.6;
            color: #5d6d7e;
            padding-left: 15px;
        }
        
        .issue-tag {
            display: inline-block;
            padding: 4px 12px;
            margin: 2px 4px;
            background: rgba(52, 152, 219, 0.1);
            border: 1px solid rgba(52, 152, 219, 0.2);
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            color: #2980b9;
            transition: all 0.3s ease;
        }
        
        .issue-tag:hover {
            background: rgba(52, 152, 219, 0.2);
            transform: scale(1.05);
        }
        
        .timestamp {
            text-align: center;
            color: #ecf0f1;
            font-size: 1.1em;
            margin-top: 30px;
            padding: 20px;
            background: rgba(52, 73, 94, 0.9);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .fab {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2980b9 0%, #3498db 100%);
            border: none;
            color: white;
            font-size: 1.5em;
            cursor: pointer;
            box-shadow: 0 10px 30px rgba(52, 152, 219, 0.5);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .fab:hover {
            transform: scale(1.1) rotate(180deg);
            box-shadow: 0 15px 40px rgba(52, 152, 219, 0.7);
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 20px;
                padding: 20px;
            }
            
            .logo-section {
                flex-direction: column;
                text-align: center;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .machine-details {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .machine-header {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
            
            .machine-id {
                font-size: 1.5em;
                justify-content: center;
            }
            
            .machine-icon {
                font-size: 1.8em;
                padding: 12px;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .machine-details {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 0 15px;
            }
            
            .header {
                padding: 15px;
            }
            
            .title-section h1 {
                font-size: 1.8em;
            }
            
            .title-section p {
                font-size: 1em;
            }
            
            .lumen-logo {
                font-size: 2.2em;
            }
        }
        
        /* Enhanced scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(52, 73, 94, 0.1);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #3498db, #2980b9);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #2980b9, #1f618d);
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <div class="live-indicator">
        <div class="live-dot"></div>
        <i class="fas fa-broadcast-tower"></i>
        LIVE
    </div>
    
    <div class="header">
        <div class="logo-section">
            <div class="lumen-logo">
                <i class="fas fa-lightbulb"></i>
                LUMEN
            </div>
            <div class="title-section">
                <h1><i class="fas fa-cogs"></i> Predictive Maintenance Dashboard</h1>
                <p><i class="fas fa-chart-line"></i> Real-time Machine Intelligence & Failure Prevention</p>
            </div>
        </div>
        
        <div class="team-credits">
            <h3><i class="fas fa-rocket"></i> Developed by Team "Trance Coders"</h3>
            <div class="team-member"><i class="fas fa-user-tie"></i> Zuha Mujawar</div>
            <div class="team-member"><i class="fas fa-user-tie"></i> Viruchith</div>
            <div class="team-member"><i class="fas fa-user-tie"></i> Pooja Shukla</div>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-server stat-icon info"></i>
                <div class="stat-value info" id="total-machines">{{ total_machines }}</div>
                <div class="stat-label"><i class="fas fa-microchip"></i> Total Machines</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-exclamation-triangle stat-icon critical"></i>
                <div class="stat-value critical" id="high-risk">{{ high_risk }}</div>
                <div class="stat-label"><i class="fas fa-fire"></i> High Risk</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-exclamation-circle stat-icon warning"></i>
                <div class="stat-value warning" id="medium-risk">{{ medium_risk }}</div>
                <div class="stat-label"><i class="fas fa-clock"></i> Medium Risk</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-check-circle stat-icon normal"></i>
                <div class="stat-value normal" id="low-risk">{{ low_risk }}</div>
                <div class="stat-label"><i class="fas fa-shield-alt"></i> Low Risk</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-card">
                <div class="chart-title">
                    <i class="fas fa-chart-pie"></i>
                    Risk Distribution
                </div>
                <div class="chart-container">
                    <canvas id="riskChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <div class="chart-title">
                    <i class="fas fa-chart-bar"></i>
                    Failure Types Analysis
                </div>
                <div class="chart-container">
                    <canvas id="failureChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="machines-section">
            <div class="section-title">
                <i class="fas fa-industry"></i>
                Machine Status Overview
            </div>
            <div id="machines-container">
                {% for machine in machines %}
                <div class="machine-card {{ machine.risk_class }}" data-machine-id="{{ machine.id }}">
                    <div class="machine-header">
                        <div class="machine-id">
                            <div class="machine-icon">
                                <i class="fas fa-microchip"></i>
                            </div>
                            <span>Machine {{ machine.id }}</span>
                        </div>
                        <div class="risk-badge {{ machine.badge_class }}">
                            <i class="fas fa-exclamation-triangle"></i>
                            {{ machine.risk_level }}
                        </div>
                    </div>
                    <div class="machine-details">
                        <div class="detail-item">
                            <div class="detail-value">
                                <i class="fas fa-tools detail-icon"></i>
                                {{ machine.failure_type }}
                            </div>
                            <div class="detail-label">Primary Risk</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">
                                <i class="fas fa-percentage detail-icon"></i>
                                {{ machine.likelihood }}
                            </div>
                            <div class="detail-label">Likelihood</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">
                                <i class="fas fa-clock detail-icon"></i>
                                {{ machine.time_to_fail }}
                            </div>
                            <div class="detail-label">Time to Fail</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-value">
                                <i class="fas fa-bug detail-icon"></i>
                                {{ machine.issues_count }}
                            </div>
                            <div class="detail-label">Active Issues</div>
                        </div>
                    </div>
                    <div class="issues-section">
                        <div class="issues-title">
                            <i class="fas fa-search"></i>
                            Diagnostic Issues
                        </div>
                        <div class="issues-content">
                            {{ machine.issues }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="timestamp">
            <i class="fas fa-clock"></i>
            Last updated: {{ timestamp }}
        </div>
    </div>
    
    <button class="fab" onclick="forceRefresh()" title="Refresh Data">
        <i class="fas fa-sync-alt"></i>
    </button>

    <script>
        const socket = io();
        
        Chart.defaults.font.family = 'Inter, sans-serif';
        Chart.defaults.color = '#2c3e50';
        
        let riskChart, failureChart;
        
        function createCharts() {
            // Risk Distribution Chart
            const riskCtx = document.getElementById('riskChart');
            if (riskCtx) {
                riskChart = new Chart(riskCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['🔴 High Risk', '🟡 Medium Risk', '🟢 Low Risk'],
                        datasets: [{
                            data: [{{ high_risk }}, {{ medium_risk }}, {{ low_risk }}],
                            backgroundColor: ['#c0392b', '#d68910', '#27ae60'],
                            borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                            borderWidth: 3,
                            cutout: '60%'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    padding: 20,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    font: { size: 14, weight: 'bold' },
                                    color: '#2c3e50'
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(44, 62, 80, 0.9)',
                                titleColor: '#ecf0f1',
                                bodyColor: '#ecf0f1',
                                borderColor: '#3498db',
                                borderWidth: 1,
                                cornerRadius: 10
                            }
                        },
                        animation: {
                            animateRotate: true,
                            animateScale: true,
                            duration: 2000
                        }
                    }
                });
            }
            
            // Failure Types Chart
            const failureCtx = document.getElementById('failureChart');
            if (failureCtx) {
                failureChart = new Chart(failureCtx, {
                    type: 'bar',
                    data: {
                        labels: ['⚡ Power Supply', '🌀 Fan', '🔥 Heat Sink', '🧠 CPU', '💾 Memory'],
                        datasets: [{
                            label: 'Failure Incidents',
                            data: [3, 2, 1, 1, 0],
                            backgroundColor: [
                                'rgba(192, 57, 43, 0.8)',
                                'rgba(214, 137, 16, 0.8)',
                                'rgba(41, 128, 185, 0.8)',
                                'rgba(142, 68, 173, 0.8)',
                                'rgba(39, 174, 96, 0.8)'
                            ],
                            borderColor: [
                                '#c0392b',
                                '#d68910',
                                '#2980b9',
                                '#8e44ad',
                                '#27ae60'
                            ],
                            borderWidth: 2,
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(189, 195, 199, 0.3)',
                                    drawBorder: false
                                },
                                ticks: {
                                    color: '#2c3e50',
                                    font: { size: 12, weight: 'bold' }
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: '#2c3e50',
                                    font: { size: 12, weight: 'bold' }
                                }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(44, 62, 80, 0.9)',
                                titleColor: '#ecf0f1',
                                bodyColor: '#ecf0f1',
                                borderColor: '#3498db',
                                borderWidth: 1,
                                cornerRadius: 10
                            }
                        },
                        animation: {
                            duration: 2000,
                            easing: 'easeOutBounce'
                        }
                    }
                });
            }
        }
        
        // Socket event handlers
        socket.on('data_update', function(data) {
            console.log('📊 Received data update:', data);
            updateDashboard(data);
        });
        
        function updateDashboard(data) {
            // Update statistics
            document.getElementById('total-machines').textContent = data.total_machines || 0;
            document.getElementById('high-risk').textContent = data.high_risk || 0;
            document.getElementById('medium-risk').textContent = data.medium_risk || 0;
            document.getElementById('low-risk').textContent = data.low_risk || 0;
            
            // Update charts
            if (riskChart) {
                riskChart.data.datasets[0].data = [
                    data.high_risk || 0,
                    data.medium_risk || 0,
                    data.low_risk || 0
                ];
                riskChart.update('active');
            }
            
            // Update timestamp
            const timestampElement = document.querySelector('.timestamp');
            if (timestampElement && data.timestamp) {
                timestampElement.innerHTML = `<i class="fas fa-clock"></i> Last updated: ${data.timestamp}`;
            }
        }
        
        function forceRefresh() {
            socket.emit('request_update');
            
            // Visual feedback
            const btn = document.querySelector('.fab i');
            if (btn) {
                btn.style.animation = 'spin 1s linear infinite';
                
                setTimeout(() => {
                    btn.style.animation = '';
                }, 1000);
            }
        }
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 Initializing Enhanced Clean Dashboard...');
            
            // Create charts
            setTimeout(() => {
                createCharts();
            }, 500);
            
            // Add machine card interactions
            initializeMachineCards();
            
            // Start auto-refresh
            setInterval(() => {
                socket.emit('request_update');
            }, 10000); // Update every 10 seconds
        });
        
        function initializeMachineCards() {
            const machineCards = document.querySelectorAll('.machine-card');
            
            machineCards.forEach(card => {
                // Add click handler for expansion
                card.addEventListener('click', function() {
                    const machineId = this.dataset.machineId;
                    console.log(`Machine ${machineId} selected`);
                    
                    // Visual feedback
                    this.style.transform = 'scale(0.98)';
                    setTimeout(() => {
                        this.style.transform = '';
                    }, 150);
                });
                
                // Add hover sound effect simulation
                card.addEventListener('mouseenter', function() {
                    const riskBadge = this.querySelector('.risk-badge');
                    if (riskBadge) {
                        riskBadge.style.animation = 'none';
                        setTimeout(() => {
                            riskBadge.style.animation = 'pulse-glow 1s ease-in-out';
                        }, 10);
                    }
                });
                
                // Animate detail items on hover
                const detailItems = card.querySelectorAll('.detail-item');
                detailItems.forEach((item, index) => {
                    item.addEventListener('mouseenter', function() {
                        this.style.animationDelay = `${index * 0.1}s`;
                        this.style.animation = 'bounce 0.6s ease';
                    });
                    
                    item.addEventListener('animationend', function() {
                        this.style.animation = '';
                    });
                });
            });
        }
        
        // Add bounce animation for detail items
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes bounce {
                0%, 20%, 53%, 80%, 100% {
                    transform: translate3d(0, 0, 0);
                }
                40%, 43% {
                    transform: translate3d(0, -8px, 0);
                }
                70% {
                    transform: translate3d(0, -4px, 0);
                }
                90% {
                    transform: translate3d(0, -2px, 0);
                }
            }
            
            @keyframes slideInUp {
                from {
                    transform: translate3d(0, 40px, 0);
                    opacity: 0;
                }
                to {
                    transform: translate3d(0, 0, 0);
                    opacity: 1;
                }
            }
            
            .machine-card {
                animation: slideInUp 0.6s ease-out forwards;
            }
            
            .machine-card:nth-child(1) { animation-delay: 0.1s; }
            .machine-card:nth-child(2) { animation-delay: 0.2s; }
            .machine-card:nth-child(3) { animation-delay: 0.3s; }
            .machine-card:nth-child(4) { animation-delay: 0.4s; }
            .machine-card:nth-child(5) { animation-delay: 0.5s; }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>'''

def get_sample_data():
    """Get sample data when real data is not available"""
    sample_machines = [
        {
            'id': 101,
            'risk_level': 'High',
            'risk_class': 'high-risk',
            'badge_class': 'risk-high',
            'failure_type': '🔧 Hard Disk',
            'likelihood': '94%',
            'time_to_fail': '⚠️ Imminent',
            'issues': '🔥 High Temp, 📳 High Vibration, ⚡ High Current',
            'issues_count': 3
        },
        {
            'id': 102,
            'risk_level': 'High',
            'risk_class': 'high-risk',
            'badge_class': 'risk-high',
            'failure_type': '⚡ Power Supply',
            'likelihood': '89%',
            'time_to_fail': '⚠️ Imminent',
            'issues': '🔥 High Temp, ⚡ High Current',
            'issues_count': 2
        },
        {
            'id': 117,
            'risk_level': 'High',
            'risk_class': 'high-risk',
            'badge_class': 'risk-high',
            'failure_type': '🔧 Hard Disk',
            'likelihood': '81%',
            'time_to_fail': '⚠️ Imminent',
            'issues': '🔥 High Temp, 📳 High Vibration, 🌀 Low Fan, ⚡ High Current',
            'issues_count': 4
        },
        {
            'id': 120,
            'risk_level': 'High',
            'risk_class': 'high-risk',
            'badge_class': 'risk-high',
            'failure_type': '🧠 Motherboard',
            'likelihood': '81%',
            'time_to_fail': '⚠️ Imminent',
            'issues': '🔥 High Temp, 📳 High Vibration, 🌀 Low Fan, ⚡ High Current',
            'issues_count': 4
        },
        {
            'id': 121,
            'risk_level': 'High',
            'risk_class': 'high-risk',
            'badge_class': 'risk-high',
            'failure_type': '⚡ Power Supply',
            'likelihood': '93%',
            'time_to_fail': '⚠️ Imminent',
            'issues': '🔥 High Temp, 📳 High Vibration, 🌀 Low Fan, ⚡ High Current',
            'issues_count': 4
        }
    ]
    
    return {
        'total_machines': 5,
        'high_risk': 5,
        'medium_risk': 0,
        'low_risk': 0,
        'machines': sample_machines,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    data = get_sample_data()
    return render_template_string(DASHBOARD_HTML, **data)

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    return jsonify(get_sample_data())

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    data = get_sample_data()
    emit('data_update', data)

@socketio.on('request_update')
def handle_update_request():
    """Handle update request from client"""
    data = get_sample_data()
    emit('data_update', data)

if __name__ == '__main__':
    print("🚀 Starting Clean Lumen Predictive Maintenance Dashboard...")
    print("=" * 60)
    print("🌐 Dashboard URL: http://127.0.0.1:5003")
    print("🔄 Real-time updates enabled via WebSocket")
    print("📊 Features:")
    print("   - Clean CSS rendering")
    print("   - Interactive charts")
    print("   - Lumen branding")
    print("   - Team Trance Coders credits")
    print("=" * 60)
    
    # Run the application
    socketio.run(app, host='127.0.0.1', port=5003, debug=True, allow_unsafe_werkzeug=True)
