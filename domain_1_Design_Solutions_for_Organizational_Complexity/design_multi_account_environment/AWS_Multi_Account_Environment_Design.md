# AWS Multi-Account Environment Design

Designing a scalable and secure multi-account AWS environment involves establishing a strong foundation using **AWS Organizations** to apply best practices for governance, security, and identity management across the entire enterprise.

The framework for building a secure, scalable multi-account environment centers heavily on **AWS Organizations** and the automation features provided by **AWS Control Tower**. This approach aligns with the AWS Well-Architected Framework principles, particularly for security and reliability.

The implementation follows a strategy centered on **isolating workloads** and organizational functions into dedicated accounts and Organizational Units (OUs).

## I. Foundational Structure: AWS Organizations and OUs

**AWS Organizations** is the global service that helps centrally manage and govern the entire environment as you scale.

*   **Management and Member Accounts:** An organization consists of one **Management Account** (the payer account) and multiple **Member Accounts**. The majority of workloads reside in member accounts to restrict access to the critical management account.

*   **Organizational Units (OUs):** Accounts are grouped into OUs based on **function, compliance requirements, or common security controls**, not the company's reporting structure. This facilitates the consistent application of policies (guardrails) across groups of accounts.

### A. Recommended Dedicated Account Structure (AWS Security Reference Architecture - SRA)

The recommended structure emphasizes separating duties and functions into dedicated accounts to isolate security tools, logs, networking, and application workloads.

| Account Category | Purpose and Security Objective |
| :--- | :--- |
| **Org Management Account** | Hosts the root of the organization; responsible for governance, managing OUs, billing, and deploying universal guardrails like **Service Control Policies (SCPs)**. |
| **Security OU: Security Tooling Account** | Dedicated to managing and operating centralized security services (e.g., aggregating findings from GuardDuty and Security Hub CSPM) and automating security alerting and response. |
| **Security OU: Log Archive Account** | Dedicated for **immutable storage** of all security and operational logs (e.g., CloudTrail organization trail, VPC Flow Logs, DNS logs) for auditing and forensics. |
| **Infrastructure OU: Network Account** | Manages the primary network gateway between applications and the broader internet. Isolates core networking services (like Transit Gateway, inspection VPCs, WAF, and Route 53) from individual workloads. |
| **Infrastructure OU: Shared Services Account** | Hosts services utilized by multiple teams and applications (e.g., Active Directory/Identity Center, messaging services). This account often acts as the **delegated administrator for IAM Identity Center**. |
| **Workloads OU: Application Account** | Hosts the enterprise applications and handles workload-specific security, access, and encryption keys. Separate accounts should be created to isolate individual applications or software services. |

## II. Governance and Guardrails with Organization Policies

AWS Organizations provides policies that enable centralized governance and enforcement across member accounts.

*   **Service Control Policies (SCPs):** These policies **specify the maximum permissions** that IAM users and roles within member accounts can utilize. SCPs act as guardrails but **do not grant permissions**; permissions must still be explicitly granted through IAM policies. SCPs **do not affect the Management Account**.

*   **Resource Control Policies (RCPs):** These centrally manage and set **maximum available permissions for resources** within accounts (for a subset of AWS services). RCPs function as resource-based guardrails.

*   **Declarative Policies:** These manage and enforce **baseline configuration** for specific services (like EC2, VPC, and EBS) at scale across the organization, independent of API calls. Examples include enforcing IMDSv2 or blocking public access for EBS snapshots.

## III. Identity and Access Management (IAM)

A strong identity foundation is crucial, emphasizing the **principle of least privilege** and reducing reliance on long-term static credentials.

*   **Delegated Administrator:** To limit access to the sensitive Management Account, administrative functions for services like **AWS IAM Identity Center** (for workforce access), **AWS Config**, and **Amazon GuardDuty** are often delegated to the **Security Tooling Account** or the **Shared Services Account**.

*   **Workforce Access (SSO):** **AWS IAM Identity Center** is the recommended service for managing workforce access, centrally managing single sign-on (SSO) to all AWS accounts and integrated applications. It connects to external identity providers (IdPs) like Active Directory or Okta using SAML 2.0.

*   **Logging Identity Activity:** The **IAM Access Analyzer** helps identify resources shared with external entities (outside the defined zone of trust). The **IAM access advisor** provides last-accessed data for services, aiding in continuously refining permissions to the principle of least privilege.

## IV. Centralized Logging and Monitoring

Traceability is maintained by monitoring and auditing all actions and changes across the environment in real time.

*   **CloudTrail Organization Trail:** This trail logs **all API events** for **all accounts** in the AWS organization and stores them in a single S3 bucket, typically in the **Log Archive Account**. Member accounts have only view-only access to this trail.

*   **Centralized Security Tools:** Services like **Amazon GuardDuty** (threat detection) and **AWS Security Hub CSPM** (security posture management) are enabled in all member accounts, but their findings are aggregated into the delegated **Security Tooling Account** for centralized visibility and management across the organization.

## V. Automation and Orchestration

Automating security best practices and infrastructure deployment is essential for scalability and consistency.

*   **AWS Control Tower:** Provides a straightforward way to set up and govern the multi-account environment (landing zone) and orchestrates services like Organizations and IAM Identity Center. Control Tower automatically applies preventative and detective **guardrails** using SCPs and AWS Config rules.

*   **Infrastructure as Code (IaC):** All infrastructure should be defined and managed as code (e.g., AWS CloudFormation) in version-controlled templates to ensure repeatable, reliable deployment, crucial for recovery and consistency across environments.

*   **Resource Sharing (AWS RAM):** **AWS Resource Access Manager (RAM)** is used to securely share centralized resources, such as VPC subnets or Route 53 Resolver rules, from central accounts (like the Network Account) to member accounts, reducing resource duplication and operational overhead.

## VI. AWS Control Tower: Detailed Implementation

**AWS Control Tower** offers the easiest way to set up and govern a secure, compliant, multi-account environment based on best practices. It automates the orchestration of several other key services, creating a **landing zone**.

### A. Automation and Governance Features

*   **Landing Zone:** Control Tower builds a well-architected, multi-account environment using AWS Organizations, AWS Service Catalog, and IAM Identity Center.

*   **Guardrails:** Control Tower enforces ongoing policy management using controls (guardrails) to prevent configurations from drifting from best practices.

    *   **Preventive Controls (SCPs):** Use Service Control Policies (SCPs) to prevent configuration changes.

    *   **Detective Controls (AWS Config/CloudTrail):** Uses **AWS Config rules** to continuously detect non-conformance and employs **CloudTrail logging** for auditing.

*   **Account Factory:** Provides a configurable template that helps automate account provisioning, standardizing new accounts with pre-approved configurations.

*   **Customizations:** The **Customizations for AWS Control Tower (CfCT)** solution allows administrators to deploy AWS SRA recommended structures, security controls, and governance baselines to accounts managed by Control Tower, using CloudFormation.
