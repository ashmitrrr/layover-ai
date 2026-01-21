# Layover AI

Layover AI is an AI powered layover planning application that helps transit travelers make the most of their stopovers using intelligent scheduling, location awareness, and realistic time buffers.

The product focuses on transforming idle layover time into safe, efficient, and enjoyable travel experiences by combining rule based logistics with modern natural language intelligence.

---

## Problem

Travelers with long layovers face uncertainty.

They do not know whether they can leave the airport safely.  
They do not know how much time is realistically available.  
They do not know which activities fit within transit constraints.  
They rely on scattered information across multiple platforms.

Layover AI solves this by providing a single structured plan that accounts for travel logistics, time buffers, and user preferences.

---

## Solution

Layover AI generates personalized layover itineraries by combining:

1. Flight context and transit hub data  
2. Layover duration and airport exit constraints  
3. City specific activity data from a structured database  
4. Risk and buffer based scheduling logic  
5. AI driven reasoning for ranking and explanation  

The result is a realistic, safe and efficient layover plan that adapts to each traveler.

---

## Core Features

1. Landside and airside decision logic  
2. Risk based buffer scoring  
3. Activity ranking by relevance and proximity  
4. Timeline visualization with Gantt style scheduling  
5. Smart fallback planning for tight layovers  
6. Structured travel reasoning explanations  
7. Real time database driven recommendations  

---

## Artificial Intelligence

Layover AI uses modern natural language processing and semantic similarity models for understanding travel intent and ranking activities.

The system uses:

Sentence Transformers for semantic embedding  
Transformer based similarity scoring  
Rule enhanced reasoning logic for travel safety  
Hybrid AI plus deterministic scheduling architecture  

This ensures that the system is not purely generative but grounded in structured planning.

---

## Data Architecture

The application uses a SQLite database as the primary source of truth.

All activities, hubs, zones, and constraints are stored in the database.

JSON files are only used for configuration and archival reference.

This approach allows future migration to scalable cloud databases without changing core logic.

---

## Timeline Engine

Layover AI uses a custom scheduling engine that:

Calculates transit and buffer time  
Allocates activity durations dynamically  
Evaluates risk based on remaining slack time  
Produces conservative and optimized schedule options  
Outputs a structured timeline used for visualization  

The visualization layer only renders the schedule.  
The planning logic is fully separated.

---

## Technology Stack

Frontend and application layer  
Python  
Streamlit  

AI and data processing  
Sentence Transformers  
PyTorch  
Scikit learn  

Database  
SQLite  

Visualization  
Plotly  

Deployment  
Docker  
Google Cloud Run  

---

## Deployment

Layover AI is containerized using Docker and deployed on Google Cloud Run.

This provides:

Stateless server execution  
Automatic scaling  
Public HTTPS endpoint  
Low cost deployment suitable for MVP validation  

The application is production accessible and not limited to local execution.

---

## Project Structure

The repository follows a modular structure with separation between UI, logic, visualization and data layers.

Assets, scripts, and configuration files are isolated for maintainability.

This structure allows smooth migration to future frontend frameworks while preserving backend intelligence.

---

## Roadmap

Version three will focus on:

1. City specific transit time intelligence  
2. Advanced buffer and confidence scoring  
3. Multi plan comparison modes  
4. User history and saved itineraries  
5. Exportable travel plans  
6. Brand identity redesign  
7. Monetization foundations  

---

## Purpose

Layover AI is both a portfolio grade engineering project and a foundation for a future travel technology product.

It demonstrates:

Product thinking  
System architecture  
AI integration  
Cloud deployment  
User experience planning  
Scalable design  

---

## Author

Ashmit Raina 

---

## Live Application

The application is deployed on Google Cloud Run.  
Public access is available through the Cloud Run endpoint.
