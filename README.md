# Cardiogenic Shock Classification Dashboard

## Overview

Cardiogenic shock is a life-threatening condition in which the heart cannot pump enough blood to meet the body's needs. This results in poor end-organ perfusion and can lead to organ failure if not recognized quickly.

This project aims to build a simple dashboard that classifies whether a patient is in cardiogenic shock based on key physiologic measurements. Using these inputs, the system will also visualize the severity of shock using the SCAI classification stages.

The goal is to demonstrate how clinical data can be used to support rapid assessment of shock and help guide escalation of care, including consideration of advanced support such as ECMO.

## Inputs

The model will evaluate several clinical measurements associated with perfusion and cardiac function:

- Mean arterial pressure (MAP)  
- Lactate  
- Cardiac output  
- Urine output  
- Creatinine  

## Outputs

The dashboard will produce two outputs:

1. **Shock Classification**  
   A binary classification indicating whether the patient is in cardiogenic shock.

2. **SCAI Shock Stage Visualization**  
   An interactive display of the patient's stage of cardiogenic shock using the SCAI classification system.

## Purpose

This project is intended as an educational demonstration of how physiological data can be integrated into a simple decision-support style interface for evaluating cardiogenic shock.