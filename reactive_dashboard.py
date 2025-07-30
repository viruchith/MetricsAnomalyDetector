#!/usr/bin/env python3
"""
Reactive Dashboard for Predictive Maintenance System
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

# Premium Dashboard HTML Template with Advanced Graphics
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 Lumen Predictive Maintenance Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --danger-gradient: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            --success-gradient: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
            --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            --glass-bg: rgba(255, 255, 255, 0.1);
            --glass-border: rgba(255, 255, 255, 0.2);
            --text-primary: #2c3e50;
            --text-secondary: #7f8c8d;
            --shadow-light: 0 8px 32px rgba(31, 38, 135, 0.37);
            --shadow-heavy: 0 15px 35px rgba(31, 38, 135, 0.5);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-attachment: fixed;
            color: var(--text-primary);
            overflow-x: hidden;
            min-height: 100vh;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Floating particles */
        .particle {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            animation: float 20s infinite linear;
        }
        
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
        }
        
        /* Header Design */
        .header {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            margin: 20px;
            border-radius: 20px;
            padding: 20px 30px;
            box-shadow: var(--shadow-light);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 20px;
            z-index: 1000;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 25px;
        }
        
        .lumen-logo {
            width: 80px;
            height: 80px;
            background: var(--danger-gradient);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 16px;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            box-shadow: var(--shadow-light);
            position: relative;
            overflow: hidden;
        }
        
        .lumen-logo::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shine 3s infinite;
        }
        
        @keyframes shine {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .title-section h1 {
            background: linear-gradient(135deg, #2c3e50, #3498db, #9b59b6);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: textGradient 3s ease infinite;
            font-size: 2.5em;
            font-weight: 800;
            margin-bottom: 5px;
        }
        
        @keyframes textGradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .title-section p {
            color: rgba(44, 62, 80, 0.8);
            font-size: 1.1em;
            font-weight: 500;
        }
        
        .team-credits {
            text-align: right;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 20px 25px;
            border-radius: 15px;
            color: white;
            box-shadow: var(--shadow-light);
            border: 1px solid var(--glass-border);
        }
        
        .team-credits h3 {
            margin-bottom: 10px;
            font-size: 1.2em;
            color: #f1c40f;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .team-member {
            font-size: 0.95em;
            margin: 3px 0;
            opacity: 0.95;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
        }
        
        /* Live Indicator */
        .live-indicator {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(39, 174, 96, 0.9);
            backdrop-filter: blur(10px);
            color: white;
            padding: 8px 15px;
            border-radius: 25px;
            font-size: 0.85em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--shadow-light);
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .live-dot {
            width: 10px;
            height: 10px;
            background: #2ecc71;
            border-radius: 50%;
            animation: pulse-live 1.5s infinite;
            box-shadow: 0 0 10px #2ecc71;
        }
        
        @keyframes pulse-live {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.7; }
        }
        
        /* Main Container */
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            padding: 35px;
            border-radius: 25px;
            text-align: center;
            box-shadow: var(--shadow-light);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .stat-card:hover::before {
            left: 100%;
        }
        
        .stat-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: var(--shadow-heavy);
        }
        
        .stat-icon {
            font-size: 3em;
            margin-bottom: 15px;
            display: block;
        }
        
        .stat-value {
            font-size: 3.5em;
            font-weight: 800;
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            background: linear-gradient(135deg, #2c3e50, #3498db);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            color: var(--text-primary);
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            opacity: 0.9;
        }
        
        .critical { color: #e74c3c; }
        .warning { color: #f39c12; }
        .normal { color: #27ae60; }
        .info { color: #3498db; }
        
        /* Charts Section */
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
            margin-bottom: 50px;
        }
        
        .chart-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            padding: 30px;
            border-radius: 25px;
            box-shadow: var(--shadow-light);
            transition: all 0.3s ease;
        }
        
        .chart-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-heavy);
        }
        
        .chart-title {
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 25px;
            color: var(--text-primary);
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
        }
        
        /* 3D Visualization */
        .viz-3d {
            background: rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 25px;
            height: 400px;
            box-shadow: var(--shadow-light);
        }
        
        /* Machines Section */
        .machines-section {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 25px;
            padding: 40px;
            box-shadow: var(--shadow-light);
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 2.2em;
            font-weight: 800;
            margin-bottom: 35px;
            color: var(--text-primary);
            text-align: center;
            position: relative;
            padding-bottom: 15px;
        }
        
        .section-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100px;
            height: 4px;
            background: var(--primary-gradient);
            border-radius: 2px;
        }
        
        .machine-card {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            border-left: 6px solid #ddd;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            border: 1px solid var(--glass-border);
        }
        
        .machine-card::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #667eea);
            background-size: 400% 400%;
            animation: borderGradient 4s ease infinite;
            border-radius: 20px;
            z-index: -1;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .machine-card:hover::before {
            opacity: 1;
        }
        
        @keyframes borderGradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .machine-card.high-risk {
            border-left-color: #e74c3c;
            background: rgba(231, 76, 60, 0.1);
            box-shadow: 0 10px 30px rgba(231, 76, 60, 0.3);
        }
        
        .machine-card.medium-risk {
            border-left-color: #f39c12;
            background: rgba(243, 156, 18, 0.1);
            box-shadow: 0 10px 30px rgba(243, 156, 18, 0.3);
        }
        
        .machine-card.low-risk {
            border-left-color: #27ae60;
            background: rgba(39, 174, 96, 0.1);
            box-shadow: 0 10px 30px rgba(39, 174, 96, 0.3);
        }
        
        .machine-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: var(--shadow-heavy);
        }
        
        .machine-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .machine-id {
            font-size: 1.6em;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .risk-badge {
            padding: 10px 25px;
            border-radius: 30px;
            color: white;
            font-weight: 700;
            font-size: 0.95em;
            text-transform: uppercase;
            box-shadow: var(--shadow-light);
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }
        
        .risk-high { 
            background: var(--danger-gradient);
            animation: urgentPulse 2s infinite;
        }
        
        @keyframes urgentPulse {
            0%, 100% { box-shadow: 0 0 20px rgba(231, 76, 60, 0.5); }
            50% { box-shadow: 0 0 30px rgba(231, 76, 60, 0.8); }
        }
        
        .risk-medium { background: var(--warning-gradient); }
        .risk-low { background: var(--success-gradient); }
        
        .machine-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 25px;
        }
        
        .detail-item {
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.3);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: var(--shadow-light);
            transition: all 0.3s ease;
            border: 1px solid var(--glass-border);
        }
        
        .detail-item:hover {
            transform: scale(1.05) rotate(1deg);
            box-shadow: var(--shadow-heavy);
        }
        
        .detail-icon {
            font-size: 2em;
            margin-bottom: 10px;
            display: block;
        }
        
        .detail-value {
            font-weight: 700;
            font-size: 1.3em;
            margin-bottom: 8px;
            color: var(--text-primary);
        }
        
        .detail-label {
            font-size: 0.9em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        
        .issues-section {
            margin-top: 20px;
            padding: 20px;
            background: rgba(255,255,255,0.25);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            border-left: 4px solid #3498db;
            box-shadow: var(--shadow-light);
        }
        
        /* Floating Action Button */
        .fab {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 70px;
            height: 70px;
            background: var(--primary-gradient);
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 1.5em;
            cursor: pointer;
            box-shadow: var(--shadow-heavy);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .fab:hover {
            transform: scale(1.15) rotate(180deg);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
        }
        
        /* Timestamp */
        .timestamp {
            text-align: center;
            padding: 25px;
            color: rgba(255,255,255,0.9);
            font-style: italic;
            font-size: 1.1em;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: var(--shadow-light);
        }
        
        /* Responsive Design */
        @media (max-width: 1200px) {
            .charts-section {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 20px;
                text-align: center;
            }
            
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .machine-details {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .title-section h1 {
                font-size: 2em;
            }
        }
        
        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Alert Animations */
        @keyframes alertBounce {
            0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
            40%, 43% { transform: translate3d(0, -30px, 0); }
            70% { transform: translate3d(0, -15px, 0); }
            90% { transform: translate3d(0,-4px,0); }
        }
        
        .alert-animation {
            animation: alertBounce 2s infinite;
        }
    </style>
        
        .header {
            background: linear-gradient(90deg, #ffffff, #f8f9fa);
            padding: 15px 30px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .lumen-logo {
            width: 120px;
            height: 60px;
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3); }
            50% { box-shadow: 0 4px 25px rgba(238, 90, 36, 0.6); }
            100% { box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3); }
        }
        
        .title-section h1 {
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 5px;
        }
        
        .title-section p {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .team-credits {
            text-align: right;
            background: linear-gradient(45deg, #667eea, #764ba2);
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .team-credits h3 {
            margin-bottom: 8px;
            font-size: 1.1em;
            color: #f1c40f;
        }
        
        .team-member {
            font-size: 0.9em;
            margin: 2px 0;
            opacity: 0.9;
        }
        
        .live-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #27ae60;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            display: flex;
            align-items: center;
            gap: 5px;
            animation: blink 1.5s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.7; }
        }
        
        .live-dot {
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: pulse-dot 1s infinite;
        }
        
        @keyframes pulse-dot {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); }
            100% { transform: scale(1); }
        }
        
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            margin: 15px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .stat-label {
            color: #666;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .critical { color: #e74c3c; }
        .warning { color: #f39c12; }
        .normal { color: #27ae60; }
        .info { color: #3498db; }
        
        .charts-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .chart-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .chart-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
        }
        
        .machines-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .section-title {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 25px;
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        .machine-card {
            background: rgba(248, 249, 250, 0.8);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 6px solid #ddd;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .machine-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, rgba(52, 152, 219, 0.5), transparent);
            animation: slide 2s infinite;
        }
        
        @keyframes slide {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .machine-card.high-risk {
            border-left-color: #e74c3c;
            background: rgba(231, 76, 60, 0.05);
            box-shadow: 0 5px 20px rgba(231, 76, 60, 0.2);
        }
        
        .machine-card.medium-risk {
            border-left-color: #f39c12;
            background: rgba(243, 156, 18, 0.05);
            box-shadow: 0 5px 20px rgba(243, 156, 18, 0.2);
        }
        
        .machine-card.low-risk {
            border-left-color: #27ae60;
            background: rgba(39, 174, 96, 0.05);
            box-shadow: 0 5px 20px rgba(39, 174, 96, 0.2);
        }
        
        .machine-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .machine-id {
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .risk-badge {
            padding: 8px 20px;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        
        .risk-high { 
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            animation: urgent-blink 1s infinite;
        }
        
        @keyframes urgent-blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.8; }
        }
        
        .risk-medium { background: linear-gradient(45deg, #f39c12, #d68910); }
        .risk-low { background: linear-gradient(45deg, #27ae60, #229954); }
        
        .machine-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .detail-item {
            text-align: center;
            padding: 15px;
            background: rgba(255,255,255,0.8);
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        
        .detail-item:hover {
            transform: scale(1.05);
        }
        
        .detail-value {
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 5px;
        }
        
        .detail-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .issues-section {
            margin-top: 15px;
            padding: 15px;
            background: rgba(255,255,255,0.6);
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .timestamp {
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
            font-style: italic;
            font-size: 1.1em;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 18px 25px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 1.1em;
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.6);
        }
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
            
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            .machine-details {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <!-- Animated Background -->
    <div class="bg-animation"></div>
    
    <!-- Floating Particles -->
    <div class="particle" style="left: 10%; width: 10px; height: 10px; animation-delay: 0s;"></div>
    <div class="particle" style="left: 20%; width: 15px; height: 15px; animation-delay: 2s;"></div>
    <div class="particle" style="left: 30%; width: 8px; height: 8px; animation-delay: 4s;"></div>
    <div class="particle" style="left: 40%; width: 12px; height: 12px; animation-delay: 6s;"></div>
    <div class="particle" style="left: 50%; width: 10px; height: 10px; animation-delay: 8s;"></div>
    <div class="particle" style="left: 60%; width: 14px; height: 14px; animation-delay: 10s;"></div>
    <div class="particle" style="left: 70%; width: 9px; height: 9px; animation-delay: 12s;"></div>
    <div class="particle" style="left: 80%; width: 11px; height: 11px; animation-delay: 14s;"></div>
    <div class="particle" style="left: 90%; width: 13px; height: 13px; animation-delay: 16s;"></div>
    
    <!-- Live Indicator -->
    <div class="live-indicator">
        <div class="live-dot"></div>
        <i class="fas fa-broadcast-tower"></i>
        LIVE
    </div>
    
    <!-- Header -->
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
    
    <!-- Main Container -->
    <div class="container">
        <!-- Statistics Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-server stat-icon info"></i>
                <div class="stat-value" id="total-machines">{{ total_machines }}</div>
                <div class="stat-label"><i class="fas fa-microchip"></i> Total Machines</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-exclamation-triangle stat-icon critical alert-animation"></i>
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
        
        <!-- Charts Section -->
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
            
            <div class="chart-card">
                <div class="chart-title">
                    <i class="fas fa-chart-line"></i>
                    Real-time Metrics
                </div>
                <div class="chart-container">
                    <canvas id="metricsChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 3D Visualization -->
        <div class="chart-card">
            <div class="chart-title">
                <i class="fas fa-cube"></i>
                3D Machine Status Visualization
            </div>
            <div id="threejs-container" class="viz-3d"></div>
        </div>
        
        <!-- Machines Section -->
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
                            <i class="fas fa-microchip"></i>
                            Machine {{ machine.id }}
                        </div>
                        <div class="risk-badge {{ machine.badge_class }}">
                            <i class="fas fa-exclamation"></i>
                            {{ machine.risk_level }}
                        </div>
                    </div>
                    <div class="machine-details">
                        <div class="detail-item">
                            <i class="fas fa-tools detail-icon"></i>
                            <div class="detail-value">{{ machine.failure_type }}</div>
                            <div class="detail-label">Primary Risk</div>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-percentage detail-icon"></i>
                            <div class="detail-value">{{ machine.likelihood }}</div>
                            <div class="detail-label">Likelihood</div>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-hourglass-half detail-icon"></i>
                            <div class="detail-value">{{ machine.time_to_fail }}</div>
                            <div class="detail-label">Time to Fail</div>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-bug detail-icon"></i>
                            <div class="detail-value">{{ machine.issues_count }}</div>
                            <div class="detail-label">Active Issues</div>
                        </div>
                    </div>
                    <div class="issues-section">
                        <strong><i class="fas fa-search"></i> Diagnostic Issues:</strong> {{ machine.issues }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Timestamp -->
        <div class="timestamp">
            <i class="fas fa-clock"></i>
            Last updated: {{ timestamp }}
        </div>
    </div>
    
    <!-- Floating Action Button -->
    <button class="fab" onclick="forceRefresh()" title="Refresh Data">
        <i class="fas fa-sync-alt"></i>
    </button>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        const socket = io();
        
        // Chart.js configuration with modern styling
        Chart.defaults.font.family = 'Inter, -apple-system, BlinkMacSystemFont, sans-serif';
        Chart.defaults.color = '#e1e8ed';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        
        let riskChart, failureChart, metricsChart;
        let scene, camera, renderer;
        
        // Advanced color schemes
        const colorSchemes = {
            primary: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'],
            risk: ['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff'],
            gradient: {
                high: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)',
                medium: 'linear-gradient(135deg, #feca57 0%, #ff9ff3 100%)',
                low: 'linear-gradient(135deg, #48dbfb 0%, #0abde3 100%)'
            }
        };
        
        function createAdvancedCharts() {
            // Risk Distribution 3D Doughnut Chart
            const riskCtx = document.getElementById('riskChart');
            if (riskCtx) {
                const gradient = riskCtx.getContext('2d');
                const bgGradient1 = gradient.createLinearGradient(0, 0, 0, 400);
                bgGradient1.addColorStop(0, '#ff6b6b');
                bgGradient1.addColorStop(1, '#ee5a24');
                
                const bgGradient2 = gradient.createLinearGradient(0, 0, 0, 400);
                bgGradient2.addColorStop(0, '#feca57');
                bgGradient2.addColorStop(1, '#ff9ff3');
                
                const bgGradient3 = gradient.createLinearGradient(0, 0, 0, 400);
                bgGradient3.addColorStop(0, '#48dbfb');
                bgGradient3.addColorStop(1, '#0abde3');
                
                riskChart = new Chart(riskCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['🔴 High Risk', '🟡 Medium Risk', '🟢 Low Risk'],
                        datasets: [{
                            data: [{{ high_risk }}, {{ medium_risk }}, {{ low_risk }}],
                            backgroundColor: [bgGradient1, bgGradient2, bgGradient3],
                            borderColor: ['#ff4757', '#ffa502', '#3742fa'],
                            borderWidth: 3,
                            hoverBorderWidth: 5,
                            cutout: '70%'
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
                                    font: { size: 14, weight: 'bold' }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                borderColor: '#667eea',
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
            
            // Failure Types 3D Bar Chart
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
                                'rgba(255, 107, 107, 0.8)',
                                'rgba(254, 202, 87, 0.8)',
                                'rgba(72, 219, 251, 0.8)',
                                'rgba(155, 89, 182, 0.8)',
                                'rgba(39, 174, 96, 0.8)'
                            ],
                            borderColor: [
                                '#ff6b6b',
                                '#feca57',
                                '#48dbfb',
                                '#9b59b6',
                                '#27ae60'
                            ],
                            borderWidth: 2,
                            borderRadius: 8,
                            borderSkipped: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.1)',
                                    drawBorder: false
                                },
                                ticks: {
                                    color: '#e1e8ed',
                                    font: { size: 12, weight: 'bold' }
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: '#e1e8ed',
                                    font: { size: 12, weight: 'bold' }
                                }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                borderColor: '#667eea',
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
            
            // Real-time Metrics Line Chart
            const metricsCtx = document.getElementById('metricsChart');
            if (metricsCtx) {
                const times = [];
                const cpuData = [];
                const tempData = [];
                
                // Generate sample time series data
                for (let i = 0; i < 10; i++) {
                    times.push(new Date(Date.now() - (9-i) * 60000).toLocaleTimeString());
                    cpuData.push(Math.random() * 100);
                    tempData.push(60 + Math.random() * 30);
                }
                
                metricsChart = new Chart(metricsCtx, {
                    type: 'line',
                    data: {
                        labels: times,
                        datasets: [{
                            label: '🖥️ CPU Usage (%)',
                            data: cpuData,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        }, {
                            label: '🌡️ Temperature (°C)',
                            data: tempData,
                            borderColor: '#f093fb',
                            backgroundColor: 'rgba(240, 147, 251, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.1)',
                                    drawBorder: false
                                },
                                ticks: {
                                    color: '#e1e8ed',
                                    font: { size: 11 }
                                }
                            },
                            x: {
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.1)',
                                    drawBorder: false
                                },
                                ticks: {
                                    color: '#e1e8ed',
                                    font: { size: 10 }
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    usePointStyle: true,
                                    font: { size: 12, weight: 'bold' }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                borderColor: '#667eea',
                                borderWidth: 1,
                                cornerRadius: 10
                            }
                        },
                        animation: {
                            duration: 1000,
                            easing: 'easeInOutQuart'
                        }
                    }
                });
            }
        }
        
        function init3DVisualization() {
            const container = document.getElementById('threejs-container');
            if (!container || typeof THREE === 'undefined') return;
            
            // Three.js setup
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setClearColor(0x000000, 0);
            container.appendChild(renderer.domElement);
            
            // Create machine cubes
            const machines = [
                { id: 1, status: 'high', color: 0xff6b6b, position: [-2, 0, 0] },
                { id: 2, status: 'medium', color: 0xfeca57, position: [0, 0, 0] },
                { id: 3, status: 'low', color: 0x48dbfb, position: [2, 0, 0] },
                { id: 4, status: 'high', color: 0xff6b6b, position: [-1, 1.5, 0] },
                { id: 5, status: 'low', color: 0x48dbfb, position: [1, 1.5, 0] }
            ];
            
            machines.forEach(machine => {
                const geometry = new THREE.BoxGeometry(0.8, 0.8, 0.8);
                const material = new THREE.MeshPhongMaterial({ 
                    color: machine.color,
                    transparent: true,
                    opacity: 0.8
                });
                const cube = new THREE.Mesh(geometry, material);
                cube.position.set(...machine.position);
                cube.userData = machine;
                scene.add(cube);
                
                // Add wireframe
                const wireframe = new THREE.WireframeGeometry(geometry);
                const line = new THREE.LineSegments(wireframe);
                line.material.color.setHex(0xffffff);
                line.material.opacity = 0.3;
                line.material.transparent = true;
                line.position.copy(cube.position);
                scene.add(line);
            });
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const pointLight = new THREE.PointLight(0xffffff, 1, 100);
            pointLight.position.set(10, 10, 10);
            scene.add(pointLight);
            
            camera.position.z = 5;
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                
                // Rotate cubes
                scene.children.forEach(child => {
                    if (child.userData && child.userData.id) {
                        child.rotation.x += 0.01;
                        child.rotation.y += 0.01;
                        
                        // Pulsing effect for high-risk machines
                        if (child.userData.status === 'high') {
                            const scale = 1 + 0.1 * Math.sin(Date.now() * 0.005);
                            child.scale.set(scale, scale, scale);
                        }
                    }
                });
                
                renderer.render(scene, camera);
            }
            animate();
            
            // Handle window resize
            window.addEventListener('resize', () => {
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            });
        }
        
        // Socket event handlers
        socket.on('data_update', function(data) {
            console.log('📊 Received data update:', data);
            updateDashboard(data);
        });
        
        socket.on('alert', function(data) {
            console.log('🚨 Received alert:', data);
            showAdvancedAlert(data);
        });
        
        function updateDashboard(data) {
            // Update statistics with animations
            animateCountUp('total-machines', data.stats ? data.stats.total_machines : data.total_machines);
            animateCountUp('high-risk', data.stats ? data.stats.high_risk : data.high_risk);
            animateCountUp('medium-risk', data.stats ? data.stats.medium_risk : data.medium_risk);
            animateCountUp('low-risk', data.stats ? data.stats.low_risk : data.low_risk);
            
            // Update charts
            if (riskChart) {
                riskChart.data.datasets[0].data = [
                    data.stats ? data.stats.high_risk : data.high_risk,
                    data.stats ? data.stats.medium_risk : data.medium_risk,
                    data.stats ? data.stats.low_risk : data.low_risk
                ];
                riskChart.update('active');
            }
            
            // Update real-time metrics
            if (metricsChart) {
                const now = new Date().toLocaleTimeString();
                metricsChart.data.labels.push(now);
                metricsChart.data.datasets[0].data.push(Math.random() * 100);
                metricsChart.data.datasets[1].data.push(60 + Math.random() * 30);
                
                // Keep only last 10 points
                if (metricsChart.data.labels.length > 10) {
                    metricsChart.data.labels.shift();
                    metricsChart.data.datasets[0].data.shift();
                    metricsChart.data.datasets[1].data.shift();
                }
                metricsChart.update('none');
            }
            
            // Update machines
            if (data.machines) {
                updateMachines(data.machines);
            }
        }
        
        function animateCountUp(elementId, targetValue) {
            const element = document.getElementById(elementId);
            if (!element) return;
            
            const currentValue = parseInt(element.textContent) || 0;
            const increment = targetValue > currentValue ? 1 : -1;
            const step = Math.abs(targetValue - currentValue) / 20;
            
            let current = currentValue;
            const animation = setInterval(() => {
                current += increment * step;
                if ((increment > 0 && current >= targetValue) || (increment < 0 && current <= targetValue)) {
                    current = targetValue;
                    clearInterval(animation);
                }
                element.textContent = Math.round(current);
            }, 50);
        }
        
        function updateMachines(machines) {
            const container = document.getElementById('machines-container');
            machines.forEach(machine => {
                const card = document.querySelector(`[data-machine-id="${machine.id}"]`);
                if (card) {
                    // Update card class for risk level with animation
                    card.className = `machine-card ${machine.risk_class}`;
                    
                    // Update badge with pulsing effect
                    const badge = card.querySelector('.risk-badge');
                    if (badge) {
                        badge.className = `risk-badge ${machine.badge_class}`;
                        badge.innerHTML = `<i class="fas fa-exclamation"></i> ${machine.risk_level}`;
                    }
                    
                    // Update details with smooth transitions
                    const details = card.querySelectorAll('.detail-value');
                    if (details.length >= 4) {
                        details[0].textContent = machine.failure_type;
                        details[1].textContent = machine.likelihood;
                        details[2].textContent = machine.time_to_fail;
                        details[3].textContent = machine.issues_count;
                    }
                    
                    // Update issues with icon
                    const issuesSection = card.querySelector('.issues-section');
                    if (issuesSection) {
                        issuesSection.innerHTML = `<strong><i class="fas fa-search"></i> Diagnostic Issues:</strong> ${machine.issues}`;
                    }
                }
            });
        }
        
        function showAdvancedAlert(alert) {
            // Create a modern floating alert with glassmorphism
            const alertDiv = document.createElement('div');
            alertDiv.className = 'floating-alert glass-effect';
            alertDiv.innerHTML = `
                <div class="alert-content">
                    <div class="alert-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="alert-text">
                        <strong>🚨 Critical Alert!</strong>
                        <p>${alert.message}</p>
                    </div>
                    <button class="alert-close" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            // Add to page with animation
            document.body.appendChild(alertDiv);
            setTimeout(() => alertDiv.classList.add('show'), 100);
            
            // Auto remove after 8 seconds
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 300);
            }, 8000);
        }
        
        function forceRefresh() {
            socket.emit('request_update');
            
            // Advanced visual feedback
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
            console.log('🚀 Initializing Advanced Dashboard...');
            
            // Create charts and 3D visualization
            setTimeout(() => {
                createAdvancedCharts();
                init3DVisualization();
            }, 500);
            
            // Start auto-refresh with staggered updates
            setInterval(() => {
                socket.emit('request_update');
            }, 5000); // Update every 5 seconds
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                    e.preventDefault();
                    forceRefresh();
                }
            });
        });
        
        // Add some fun easter eggs
        let clickCount = 0;
        const lumenLogo = document.querySelector('.lumen-logo');
        if (lumenLogo) {
            lumenLogo.addEventListener('click', function() {
                clickCount++;
                if (clickCount === 5) {
                    this.style.animation = 'rainbow 2s infinite';
                    setTimeout(() => {
                        this.style.animation = '';
                        clickCount = 0;
                    }, 4000);
                }
            });
        }
    </script>
</body>
</html>
"""

def get_dashboard_data():
    """Get current prediction data for dashboard"""
    try:
        # Check if training history exists
        history_file = "training_history/training_log.csv"
        if not os.path.exists(history_file):
            return get_sample_data()
        
        # Try to get latest predictions
        models_dir = "models"
        if not os.path.exists(models_dir):
            return get_sample_data()
        
        # Get data from the latest input files
        import glob
        csv_files = glob.glob("input*.csv")
        if not csv_files:
            return get_sample_data()
        
        # Load the most recent data
        latest_file = sorted(csv_files)[-1]
        df = pd.read_csv(latest_file)
        
        # Get unique machines
        machines = []
        machine_ids = df['machine_id'].unique()
        
        for machine_id in machine_ids:
            machine_data = df[df['machine_id'] == machine_id].iloc[-1]  # Latest record
            
            # Simulate risk calculation (simplified)
            temp = machine_data.get('temperature', 70)
            vibration = machine_data.get('vibration', 0.1)
            current = machine_data.get('current', 10)
            fan_speed = machine_data.get('fan_speed', 1500)
            
            # Calculate risk score
            risk_score = 0
            issues = []
            if temp > 80:
                risk_score += 0.3
                issues.append("🔥 High Temp")
            if vibration > 0.2:
                risk_score += 0.3
                issues.append("📳 High Vibration")
            if current > 12:
                risk_score += 0.2
                issues.append("⚡ High Current")
            if fan_speed < 1200:
                risk_score += 0.2
                issues.append("🌀 Low Fan Speed")
            
            # Determine risk level
            if risk_score > 0.6:
                risk_level = "High"
                risk_class = "high-risk"
                badge_class = "risk-high"
                time_to_fail = "⚠️ Imminent"
            elif risk_score > 0.3:
                risk_level = "Medium"
                risk_class = "medium-risk"
                badge_class = "risk-medium"
                time_to_fail = "⏱️ 2-4 hours"
            else:
                risk_level = "Low"
                risk_class = "low-risk"
                badge_class = "risk-low"
                time_to_fail = "✅ Stable"
            
            # Determine primary failure type
            failure_types = ['🔧 Hard Disk', '⚡ Power Supply', '🌀 Fan', '🧠 Motherboard', '📡 Network Card']
            failure_type = failure_types[hash(str(machine_id)) % len(failure_types)]
            
            machines.append({
                'id': int(machine_id),  # Convert to regular int
                'risk_level': risk_level,
                'risk_class': risk_class,
                'badge_class': badge_class,
                'failure_type': failure_type,
                'likelihood': f"{risk_score*100:.0f}%",
                'time_to_fail': time_to_fail,
                'issues': ", ".join(issues) if issues else "All systems normal",
                'issues_count': len(issues)
            })
        
        # Calculate summary stats
        total_machines = len(machines)
        high_risk = len([m for m in machines if m['risk_level'] == 'High'])
        medium_risk = len([m for m in machines if m['risk_level'] == 'Medium'])
        low_risk = len([m for m in machines if m['risk_level'] == 'Low'])
        
        return {
            'total_machines': total_machines,
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'machines': sorted(machines, key=lambda x: x['risk_level'], reverse=True),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        return get_sample_data()

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
    data = get_dashboard_data()
    return render_template_string(DASHBOARD_HTML, **data)

@app.route('/api/data')
def api_data():
    """API endpoint for dashboard data"""
    return jsonify(get_dashboard_data())

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    data = get_dashboard_data()
    # Convert numpy int64 to regular int for JSON serialization
    if isinstance(data, dict):
        for key, value in data.items():
            if hasattr(value, 'item'):  # numpy scalar
                data[key] = value.item()
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if hasattr(v, 'item'):
                                item[k] = v.item()
    emit('data_update', data)

@socketio.on('request_update')
def handle_update_request():
    """Handle update request from client"""
    data = get_dashboard_data()
    # Convert numpy int64 to regular int for JSON serialization
    if isinstance(data, dict):
        for key, value in data.items():
            if hasattr(value, 'item'):  # numpy scalar
                data[key] = value.item()
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if hasattr(v, 'item'):
                                item[k] = v.item()
    emit('data_update', data)

def background_data_update():
    """Background thread to push updates every 30 seconds"""
    while True:
        time.sleep(30)
        data = get_dashboard_data()
        socketio.emit('data_update', data)

if __name__ == '__main__':
    print("🚀 Starting Lumen Predictive Maintenance Dashboard...")
    print("=" * 60)
    print("🌐 Dashboard URL: http://127.0.0.1:5002")
    print("🔄 Real-time updates enabled via WebSocket")
    print("📊 Features:")
    print("   - Live data streaming")
    print("   - Interactive charts")
    print("   - Mobile responsive design")
    print("   - Lumen branding")
    print("   - Team Trance Coders credits")
    print("=" * 60)
    
    # Start background update thread
    update_thread = threading.Thread(target=background_data_update)
    update_thread.daemon = True
    update_thread.start()
    
    # Run the application
    socketio.run(app, host='127.0.0.1', port=5002, debug=True, allow_unsafe_werkzeug=True)
