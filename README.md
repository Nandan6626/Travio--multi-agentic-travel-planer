# ✈️ Travio – Multi-Agentic AI Travel Planner

[![XERJ Corpus Hub Contributor](https://hub.xerj.org/contributors/Nandan6626/badge.svg)](https://hub.xerj.org/contributors/Nandan6626)

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/Nandan6626/Travio--multi-agentic-travel-planer)

**Travio** is an AI-powered multi-agent travel planning system that transforms natural-language travel requests into personalized, structured travel itineraries.

Instead of relying on a single AI model, Travio uses specialized AI agents coordinated through an Orchestrator Agent to plan different aspects of a journey, including flights, hotels, activities, places, and weather.

The system combines multi-agent orchestration, external data retrieval, and intelligent itinerary generation to make travel planning smarter and more efficient.

---

## 🌍 Problem Statement

Planning a trip involves researching multiple platforms for flights, accommodation, weather conditions, tourist attractions, and activities.

This process is often time-consuming and requires users to manually compare information from different sources.

Travio aims to simplify this process through an intelligent multi-agent architecture that coordinates different travel-planning tasks and generates a unified itinerary.

## 🎯 Objectives

- Develop an intelligent multi-agent travel planning system.
- Coordinate specialized agents using LangGraph.
- Retrieve and organize travel information from external APIs and datasets.
- Generate personalized day-wise travel itineraries.
- Validate travel plans against budget, weather, and user preferences.
- Minimize hallucinations by grounding recommendations in retrieved information.

## 🤖 Key Features

- **AI-Powered Travel Planning:** Understands natural-language travel requests.
- **Multi-Agent Architecture:** Uses specialized agents for different travel tasks.
- **Flight Agent:** Retrieves and organizes flight information.
- **Hotel Agent:** Finds suitable accommodation options.
- **Activity & Places Agent:** Identifies attractions, destinations, and activities.
- **Weather Agent:** Retrieves weather information for travel destinations.
- **Budget Validation:** Evaluates the combined plan against the user's budget.
- **Itinerary Generation:** Creates structured, day-wise travel schedules.
- **Intelligent Coordination:** Uses an Orchestrator Agent to coordinate specialized agents.

## 🏗️ System Architecture

Travio follows a multi-agent architecture coordinated by an Orchestrator Agent.

### Agent Workflow

1. User submits a natural-language travel request.
2. The Orchestrator Agent understands and decomposes the request.
3. Specialized agents independently retrieve relevant information.
4. Agents return structured JSON responses.
5. A validation and scoring engine checks budget, weather, and preference constraints.
6. The Orchestrator coordinates revisions when the plan is infeasible.
7. The Itinerary Agent assembles the final day-wise travel plan.
8. The frontend displays the generated itinerary.

### Architecture Overview

```text
             USER REQUEST
                   |
                   v
          ORCHESTRATOR AGENT
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
    FLIGHT       HOTEL      WEATHER
     AGENT       AGENT       AGENT
       |           |           |
       +-----------+-----------+
                   |
             ACTIVITY / PLACES
                   AGENT
                   |
                   v
          STRUCTURED RESPONSES
                   |
                   v
          VALIDATION & SCORING
                   |
                   v
          ITINERARY GENERATION
                   |
                   v
            FINAL TRAVEL PLAN
                   |
                   v
               USER APP
```

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React Native, Expo, JavaScript, JSX |
| Backend | Python, FastAPI |
| Multi-Agent Framework | LangGraph |
| Database | PostgreSQL |
| API Development | REST APIs |
| Data Processing | Python |
| Version Control | Git, GitHub |

## 📂 Project Structure

The project is organized into frontend and backend components.

```text
Travio/
│
├── frontend/
│   └── React Native Expo application
│
├── backend/
│   └── FastAPI application
│
├── README.md
└── .gitignore
```

*Note: Update this structure to match the actual repository folders.*

## 🚀 Development Progress

### Milestone 1 – Foundation
- FastAPI backend health endpoint implemented.
- React Native Expo application migrated to JavaScript and JSX.
- Dynamic Android LAN and Emulator IP resolution implemented.

### Milestone 2 – Backend Development
- FastAPI modular monolith foundation.
- PostgreSQL integration.
- Backend development and API organization.

### Upcoming Development
- Specialized agent implementation.
- LangGraph-based orchestration.
- External travel API integrations.
- Budget validation and optimization.
- Intelligent itinerary generation.
- Frontend and backend integration.

*Development status is evolving as new milestones are completed.*

## 🔮 Future Enhancements

- Real-time flight and hotel information.
- Personalized recommendations based on travel preferences.
- Multi-city trip planning.
- Interactive travel maps.
- Cost optimization and alternative itineraries.
- Improved agent collaboration and error recovery.

## 👨‍💻 Developer

**Nandan Manjunath Naik**

Computer Science and Business Systems Engineering Student

- GitHub: [@Nandan6626](https://github.com/Nandan6626)
- XERJ Contributor Profile: [View Profile](https://hub.xerj.org/contributors/Nandan6626)

## 🌟 Project Recognition

Travio has been selected for inclusion in the **XERJ Corpus Hub**, an open reference corpus designed to help AI coding agents retrieve real-world code implementations.
[View XERJ Contributor Profile](https://hub.xerj.org/contributors/Nandan6626)
---
## 📄 License
Refer to the repository's LICENSE file for licensing information.
---
⭐ If you find this project interesting, consider giving the repository a star!
