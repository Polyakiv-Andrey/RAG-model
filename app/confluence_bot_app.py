from bridge.bridge_v1 import AzureConnector
from confluence import read_doc, update_doc
from util import parse_content, find_data_in_cell, update_cell, generate_content
import asyncio

PROMPT = (
    'Analyze this provided infrastructure data for FedRAMP High certification compliance. For each control gap, provide: '
    'Topic name: {}'
    '1. Analysis: Assess compliance with specific FedRAMP High controls (cite control IDs'
    '2. Recommendation: Concise, actionable steps to remediate gaps'
    '3. Focus: Concentrate on interconnections, 3-party services, cloud components, FedRAMP requirements for program languages'
    '4. Artifacts: Existing tools or processes that could serve as evidence'
    'Limit responses to 100 tokens. Prioritize critical security gaps. No introductions needed.'
)

prompts = [
    PROMPT,
    "Assess the provided infrastructure for FedRAMP High compliance. For each identified gap, respond with: "
    "Topic: {} "
    "- Compliance Analysis: Does it meet FedRAMP High requirements? Cite control IDs. "
    "- Remediation Steps: Clear, practical actions to fix the gap. "
    "- Key Focus Areas: Cloud security, third-party dependencies, programming language compliance. "
    "- Supporting Artifacts: Relevant tools, logs, or processes that validate compliance. "
    "Keep responses within 100 tokens, focusing on critical security concerns.",

    "Review this infrastructure data against FedRAMP High standards. Address control gaps with: "
    "Topic: {} "
    "- Gap Analysis: Identify missing compliance elements (cite control IDs). "
    "- Recommended Actions: Immediate steps to close the gap. "
    "- Risk Areas: Highlight cloud architecture, external dependencies, and programming security. "
    "- Compliance Artifacts: List existing tools, policies, or logs supporting compliance. "
    "Response must be under 100 tokens, prioritizing key risks.",

    "Analyze the infrastructure for FedRAMP High compliance. Your response should include: "
    "Topic: {} "
    "- Status: Compliant or not? Reference applicable control IDs. "
    "- Mitigation Strategy: Short, actionable remediation plan. "
    "- Risk Areas: Cloud services, integrations, FedRAMP programming requirements. "
    "- Supporting Evidence: Tools, reports, or processes demonstrating compliance. "
    "Limit to 100 tokens. Focus on high-risk issues.",

    "Evaluate the given infrastructure for FedRAMP High security gaps. Your response should cover: "
    "Topic: {} "
    "- Compliance Check: Assess against FedRAMP High controls (cite IDs). "
    "- Remediation Plan: Concise steps to address non-compliance. "
    "- Primary Focus: Cloud security, third-party integrations, programming standards. "
    "- Artifacts for Proof: Existing logs, security tools, and policies. "
    "Response must be brief (100 tokens max), prioritizing severe vulnerabilities.",

    "Perform a FedRAMP High compliance review of the provided infrastructure. Output format: "
    "Topic: {} "
    "- Assessment: Compliance status with control IDs. "
    "- Fixes: Specific remediation steps. "
    "- Security Focus: Cloud infrastructure, external services, programming security. "
    "- Verification Artifacts: Tools and policies to support compliance. "
    "Limit response to 100 tokens, emphasizing critical security flaws.",

    "Audit the infrastructure for FedRAMP High compliance gaps. Provide findings as follows: "
    "Topic: {} "
    "- Current Compliance: Does it align with FedRAMP High? Cite control IDs. "
    "- Remediation Steps: Short and actionable. "
    "- Risk Priorities: Cloud components, third-party dependencies, programming compliance. "
    "- Artifacts: Identify relevant tools, logs, and security policies. "
    "Keep responses concise (100 tokens max), prioritizing critical security gaps.",

    "Assess infrastructure security under FedRAMP High. Your output format: "
    "Topic: {} "
    "- Control Status: Compliance check (cite FedRAMP control IDs). "
    "- Fixes Required: Key recommendations to resolve gaps. "
    "- High-Risk Areas: Cloud security, external services, programming requirements. "
    "- Artifacts for Validation: Security tools, monitoring logs, policies. "
    "Keep responses under 100 tokens, prioritizing major security risks.",

    "Analyze infrastructure security for FedRAMP High. Provide a structured response: "
    "Topic: {} "
    "- Compliance Review: Does it meet FedRAMP standards? Reference control IDs. "
    "- Recommended Fixes: Specific actions for remediation. "
    "- Critical Security Areas: Cloud security, dependencies, language compliance. "
    "- Supporting Artifacts: Logs, tools, security configurations. "
    "Limit response to 100 tokens. Focus on high-risk gaps first.",

    "Perform an infrastructure compliance check for FedRAMP High. Respond with: "
    "Topic: {} "
    "- Security Assessment: Evaluate FedRAMP compliance (cite control IDs). "
    "- Mitigation Plan: Actionable next steps. "
    "- Key Risks: Cloud architecture, integrations, programming security. "
    "- Verification Artifacts: Relevant security evidence. "
    "Keep responses concise (max 100 tokens), focusing on major security flaws.",

    "Check infrastructure compliance with FedRAMP High. Format response as: "
    "Topic: {} "
    "- Compliance Check: Status vs. FedRAMP High controls (reference control IDs). "
    "- Required Actions: Direct and effective remediation. "
    "- Key Security Areas: Cloud security, third-party dependencies, programming risks. "
    "- Artifacts for Compliance: List supporting logs, tools, or reports. "
    "Restrict responses to 100 tokens, prioritizing severe vulnerabilities.",

    "Assess the infrastructure setup against FedRAMP High requirements. Deliver: "
    "Topic: {} "
    "- Gap Identification: Control compliance status (cite IDs). "
    "- Recommended Fixes: Actionable steps to resolve compliance issues. "
    "- Focus Areas: Cloud, integrations, programming security measures. "
    "- Supporting Artifacts: Security logs, monitoring tools, policy documentation. "
    "Limit response to 100 tokens, emphasizing critical security concerns.",

    "Evaluate FedRAMP High compliance of the given infrastructure. Include: "
    "Topic: {} "
    "- Control Compliance: Status against FedRAMP controls (cite IDs). "
    "- Fix Recommendations: Steps for remediation. "
    "- Security Priorities: Cloud security, dependencies, compliance standards. "
    "- Artifacts as Proof: Tools, security frameworks, monitoring logs. "
    "Response limited to 100 tokens. Highlight the most pressing gaps.",

    "Analyze compliance gaps in this infrastructure per FedRAMP High. Respond with: "
    "Topic: {} "
    "- Current Status: Compliance assessment (cite control IDs). "
    "- Solution Plan: Key remediation actions. "
    "- Major Risks: Cloud security, programming security, integrations. "
    "- Artifacts for Evidence: Security policies, monitoring tools. "
    "Keep response under 100 tokens. Prioritize critical gaps.",

    "Perform a compliance analysis for FedRAMP High. Your response should follow: "
    "Topic: {} "
    "- Assessment: Compliance status based on FedRAMP control IDs. "
    "- Remediation: Actionable recommendations. "
    "- Key Risk Areas: Cloud components, external dependencies, language security. "
    "- Artifacts Available: Supporting logs, policies, tools. "
    "Limit responses to 100 tokens, focusing on major security weaknesses.",

    "Check infrastructure for FedRAMP High compliance. Deliver a structured response: "
    "Topic: {} "
    "- Compliance Check: Identify alignment with control IDs. "
    "- Remediation Actions: Step-by-step fixes. "
    "- Security Considerations: Cloud usage, external dependencies, security controls. "
    "- Supporting Evidence: Security tools, logs, policy documents. "
    "Keep response under 100 tokens. Prioritize security gaps.",

    "Evaluate security gaps in this infrastructure under FedRAMP High. Answer using: "
    "Topic: {} "
    "- Analysis: Review compliance (cite control IDs). "
    "- Fixes: Direct remediation steps. "
    "- Main Concerns: Cloud architecture, integrations, programming security. "
    "- Compliance Artifacts: Logs, tools, documentation. "
    "Limit responses to 100 tokens. Focus on major vulnerabilities.",

    "Assess this infrastructure against FedRAMP High. Your response should include: "
    "Topic: {} "
    "- Compliance Review: Identify gaps (reference control IDs). "
    "- Solutions: Key steps to fix non-compliance. "
    "- Focus Areas: Security interconnections, cloud risks, programming standards. "
    "- Artifacts: List tools, policies, logs for validation. "
    "Limit response to 100 tokens, prioritizing key security risks."
]


def shard_asking(model, initial_data, ai_model, prompt):
    initial_data = initial_data.split('--')
    answers = ''

    answers += f'Prompt used:\n\n{prompt}\n\n'
    for i, data in enumerate(initial_data):
        print(f'Asking model, iteration {i + 1}')
        if ai_model == 'internal':
            answers += f'{model.ask(prompt + data)}' + '\n'
        else:
            answers += model.process_fedramp_query(data, prompt) + '\n'

    return answers


async def run_program(rag, ai_model='internal'):
    old_info = ''
    connector = AzureConnector()

    print('Program started with model: ' + ai_model)
    while True:
        await asyncio.sleep(2)
        content = read_doc()
        table = parse_content(content)
        initial_data = find_data_in_cell(table, 1)
        ai_answer = find_data_in_cell(table, 3)
        if not old_info:
            for prompt in prompts:
                if initial_data and initial_data != old_info:
                    if ai_model == 'internal':
                        answer = shard_asking(rag, initial_data, ai_model, prompt)
                    else:
                        answer = shard_asking(connector, initial_data, ai_model, prompt)

                    update_cell(4, table, answer)
                    new_content = generate_content(table)
                    print('Updating Confluence document --->')
                    update_doc(new_content)
        if not initial_data and ai_answer:
            update_cell(4, table, '')
            new_content = generate_content(table)
            update_doc(new_content)
        old_info = initial_data
