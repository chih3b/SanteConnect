"""
Agent de génération de rapports médicaux
Génère des rapports professionnels pour les médecins
"""

from typing import Dict, List
from datetime import datetime
import json


class ReportGeneratorAgent:
    """Génère des rapports médicaux détaillés"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.report_count = 0
        print("✅ ReportGeneratorAgent initialisé")
    
    def generate_medical_report(self, conversation_data: Dict, patient_info: Dict, session_id: str) -> Dict:
        """Génère un rapport médical complet"""
        self.report_count += 1
        print(f"📝 Génération du rapport médical #{self.report_count}")
        
        symptoms_data = conversation_data.get("symptoms", {})
        diagnosis_data = conversation_data.get("diagnosis", {})
        
        report_content = self._generate_report_content(symptoms_data, diagnosis_data, patient_info)
        
        report_html = self._format_html_report(report_content, patient_info, session_id, symptoms_data, diagnosis_data)
        report_text = self._format_text_report(report_content, patient_info, session_id, symptoms_data, diagnosis_data)
        
        return {
            "report_html": report_html,
            "report_text": report_text,
            "report_json": report_content,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
    
    def _generate_report_content(self, symptoms_data: Dict, diagnosis_data: Dict, patient_info: Dict) -> Dict:
        """Génère le contenu du rapport"""
        primary = diagnosis_data.get("primary_disease", {}) or {}
        symptoms = symptoms_data.get("symptoms", [])
        
        # Get treatment - check both 'treatment' (string) and 'treatments' (list)
        treatment = primary.get("treatment", "")
        treatments_list = primary.get("treatments", [])
        
        # Build treatment recommendations
        recommandations = []
        if treatment:
            recommandations.append(treatment)
        if treatments_list:
            for t in treatments_list:
                if t and t not in recommandations:
                    recommandations.append(t)
        
        # Add when_to_consult if available
        when_to_consult = primary.get("when_to_consult", "")
        if when_to_consult:
            recommandations.append(f"Consulter si: {when_to_consult}")
        
        # Check emergency status
        is_emergency = primary.get("is_emergency", False)
        urgency_level = "CRITIQUE - URGENCE" if is_emergency else diagnosis_data.get("urgency_level", "Modéré")
        
        # Build executive summary
        emergency_warning = "⚠️ URGENCE MÉDICALE - " if is_emergency else ""
        resume = f"{emergency_warning}Patient présentant {len(symptoms)} symptômes. Diagnostic présomptif: {primary.get('name', 'Non déterminé')}. Niveau d'urgence: {urgency_level}."
        
        return {
            "resume_executif": resume,
            "anamnese": "Consultation effectuée via assistant médical IA Dr. Raif.",
            "symptomes_presentes": symptoms,
            "analyse_diagnostique": {
                "diagnostic_principal": primary.get("name", "Non déterminé"),
                "confiance": f"{primary.get('confidence', 0):.0%}",
                "raisonnement": primary.get("reasoning", "Basé sur l'analyse des symptômes"),
                "is_emergency": is_emergency
            },
            "diagnostics_differentiels": [d.get("name", "") for d in diagnosis_data.get("possible_diseases", [])[:4]],
            "evaluation_urgence": {
                "niveau": urgency_level,
                "justification": diagnosis_data.get("urgency_reasoning", "Évaluation basée sur les symptômes"),
                "is_emergency": is_emergency
            },
            "recommandations_therapeutiques": recommandations[:8] if recommandations else ["Consultation médicale recommandée"],
            "plan_suivi": ["Consultation médicale recommandée", "Surveillance des symptômes", "Retour si aggravation"],
            "observations": "Rapport généré par Dr. Raif - Assistant Médical IA.",
            "is_emergency": is_emergency
        }
    
    def _format_html_report(self, report_content: Dict, patient_info: Dict, session_id: str, symptoms_data: Dict, diagnosis_data: Dict) -> str:
        """Formate le rapport en HTML"""
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")
        primary = diagnosis_data.get('primary_disease', {})
        urgency_level = report_content.get('evaluation_urgence', {}).get('niveau', 'Modéré')
        
        urgency_class = 'critique' if 'critique' in urgency_level.lower() else \
                       'eleve' if 'élev' in urgency_level.lower() else \
                       'faible' if 'faib' in urgency_level.lower() else 'modere'
        
        symptoms_html = ""
        for s in report_content.get('symptomes_presentes', []):
            symptoms_html += f"<li>{s}</li>"
        
        treatments_html = ""
        for t in report_content.get('recommandations_therapeutiques', []):
            treatments_html += f"<li>{t}</li>"
        
        diff_html = ""
        for i, d in enumerate(report_content.get('diagnostics_differentiels', [])[:4], 1):
            diff_html += f'<div class="diff-item"><strong>{i}.</strong> {d}</div>'
        
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport Médical - {patient_info.get('name', 'Patient')}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f7fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        .section h2 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .urgency-badge {{ display: inline-block; padding: 10px 20px; border-radius: 25px; font-weight: bold; }}
        .urgency-critique {{ background: #dc3545; color: white; }}
        .urgency-eleve {{ background: #fd7e14; color: white; }}
        .urgency-modere {{ background: #ffc107; color: #333; }}
        .urgency-faible {{ background: #28a745; color: white; }}
        .symptom-list li {{ padding: 12px; margin: 8px 0; background: #ffebee; border-left: 5px solid #dc3545; border-radius: 8px; }}
        .treatment-list li {{ padding: 12px; margin: 8px 0; background: #e3f2fd; border-left: 5px solid #2196f3; border-radius: 8px; }}
        .diagnosis-box {{ background: #e8f5e9; border: 2px solid #4caf50; padding: 25px; border-radius: 12px; margin: 20px 0; }}
        .diagnosis-box h3 {{ color: #2e7d32; }}
        .diff-item {{ background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #6c757d; }}
        .warning-box {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 12px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; margin-top: 40px; padding: 25px; border-top: 3px solid #667eea; }}
        ul {{ list-style: none; padding: 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 RAPPORT MÉDICAL</h1>
        <p>Généré par Dr. Raif - Assistant Médical IA</p>
        <p><strong>Patient:</strong> {patient_info.get('name', 'Non renseigné')} | <strong>Date:</strong> {timestamp}</p>
    </div>

    <div class="section">
        <h2>📋 RÉSUMÉ</h2>
        <p>{report_content.get('resume_executif', '')}</p>
    </div>

    <div class="section">
        <h2>🔴 SYMPTÔMES PRÉSENTÉS</h2>
        <ul class="symptom-list">{symptoms_html}</ul>
    </div>

    <div class="section">
        <h2>🏥 DIAGNOSTIC</h2>
        <div class="diagnosis-box">
            <h3>Diagnostic Présomptif</h3>
            <p style="font-size: 20px; font-weight: bold; color: #2e7d32;">{report_content.get('analyse_diagnostique', {}).get('diagnostic_principal', 'N/A')}</p>
            <p><strong>Confiance:</strong> {report_content.get('analyse_diagnostique', {}).get('confiance', 'N/A')}</p>
            <p><strong>Raisonnement:</strong> {report_content.get('analyse_diagnostique', {}).get('raisonnement', '')}</p>
        </div>
    </div>

    <div class="section">
        <h2>🔍 DIAGNOSTICS DIFFÉRENTIELS</h2>
        {diff_html}
    </div>

    <div class="section">
        <h2>⚠️ URGENCE</h2>
        <span class="urgency-badge urgency-{urgency_class}">{urgency_level}</span>
        <p style="margin-top: 15px;">{report_content.get('evaluation_urgence', {}).get('justification', '')}</p>
    </div>

    <div class="section">
        <h2>💊 TRAITEMENTS RECOMMANDÉS</h2>
        <ul class="treatment-list">{treatments_html}</ul>
    </div>

    <div class="warning-box">
        <p><strong>⚠️ AVERTISSEMENT</strong></p>
        <p>Ce rapport est généré par IA et ne remplace pas un diagnostic médical professionnel.</p>
    </div>

    <div class="footer">
        <p><strong>🏥 Dr. Raif - Assistant Médical IA</strong></p>
        <p>Rapport généré le {timestamp} | Session: {session_id[:12]}...</p>
    </div>
</body>
</html>"""
    
    def _format_text_report(self, report_content: Dict, patient_info: Dict, session_id: str, symptoms_data: Dict, diagnosis_data: Dict) -> str:
        """Formate le rapport en texte"""
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")
        
        symptoms_text = "\n".join([f"   • {s}" for s in report_content.get('symptomes_presentes', [])])
        treatments_text = "\n".join([f"   {i}. {t}" for i, t in enumerate(report_content.get('recommandations_therapeutiques', []), 1)])
        diff_text = "\n".join([f"   {i}. {d}" for i, d in enumerate(report_content.get('diagnostics_differentiels', []), 1)])
        
        return f"""
================================================================================
                              RAPPORT MÉDICAL
================================================================================
Généré par: Dr. Raif - Assistant Médical IA
Date: {timestamp}
Session: {session_id}
================================================================================

PATIENT: {patient_info.get('name', 'Non renseigné')}

1. RÉSUMÉ
---------
{report_content.get('resume_executif', '')}

2. SYMPTÔMES PRÉSENTÉS
----------------------
{symptoms_text}

3. DIAGNOSTIC
-------------
Diagnostic: {report_content.get('analyse_diagnostique', {}).get('diagnostic_principal', 'N/A')}
Confiance: {report_content.get('analyse_diagnostique', {}).get('confiance', 'N/A')}
Raisonnement: {report_content.get('analyse_diagnostique', {}).get('raisonnement', '')}

4. DIAGNOSTICS DIFFÉRENTIELS
----------------------------
{diff_text}

5. URGENCE
----------
Niveau: {report_content.get('evaluation_urgence', {}).get('niveau', 'Modéré')}
Justification: {report_content.get('evaluation_urgence', {}).get('justification', '')}

6. TRAITEMENTS RECOMMANDÉS
--------------------------
{treatments_text}

================================================================================
                         AVERTISSEMENT
================================================================================
Ce rapport est généré par IA et ne remplace pas un diagnostic médical.
En cas d'urgence, appelez le 15 (SAMU) ou le 112.
================================================================================
                    Dr. Raif - Assistant Médical IA
================================================================================
"""
