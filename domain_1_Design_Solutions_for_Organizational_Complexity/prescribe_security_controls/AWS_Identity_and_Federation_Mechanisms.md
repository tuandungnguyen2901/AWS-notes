# AWS Identity and Federation Mechanisms

Identity providers (IdPs) and federation in AWS are foundational elements of the security architecture, enabling centralized, secure access for human users (workforce identities) and applications (machine identities) using temporary credentials instead of long-term access keys. Federation establishes a trust system between two parties—an identity provider and an AWS service—to authenticate users and authorize their access to AWS resources.

## I. Workforce Identity Management and Federation

AWS recommends using federation with an IdP to access AWS services, providing workforce identities with temporary credentials by assuming roles.

### A. AWS IAM Identity Center (Successor to AWS Single Sign-On)

AWS IAM Identity Center (IAM Identity Center) is the **recommended service** for managing workforce access to AWS accounts and applications across a multi-account environment. It centrally manages SSO access and user permissions for AWS resources.

*   **Centralization and Control:** IAM Identity Center helps you centrally manage SSO access to all your AWS accounts, principals, and cloud workloads. It provides a single user portal where end-users can find and access their assigned accounts and applications.

*   **External Identity Providers (IdPs):** IAM Identity Center integrates with external identity sources using **SAML 2.0**. Supported external IdPs include Microsoft Entra ID, Okta, Google Workspace, Ping Identity, and JumpCloud.

*   **Provisioning:** It supports automatic provisioning and deprovisioning of users and groups (synchronization) via the **System for Cross-Domain Identity Management (SCIM) v2.0 standard** for supported external IdPs.

*   **Active Directory Integration:** IAM Identity Center can connect to AWS Managed Microsoft Active Directory (AD) or self-managed Active Directory domains, using AD Connector or a two-way trust relationship, respectively, as an identity source. The **Shared Services account** is often designated as the delegated administrator for IAM Identity Center if Active Directory is used, as the directory should reside in the same account as the delegated administrator.

*   **Access Control:** It supports **Attribute-Based Access Control (ABAC)**, allowing the definition of fine-grained permissions using attributes like job role or department via the `aws:PrincipalTag` global condition key in custom policies.

*   **Security:** Using IAM Identity Center enables users to access AWS resources using **temporary credentials**, eliminating the need for long-term IAM users or API keys.

### B. IAM Federation (SAML 2.0)

IAM federation is an alternative to IAM Identity Center that uses SAML 2.0 or OpenID Connect (OIDC) to establish a trust system.

*   **Mechanism:** An Identity Provider authenticates the user and supplies authorization context data to IAM, which then controls access to AWS resources.

*   **Pattern:** In a multi-account environment using IAM federation, a separate SAML trust relationship is typically established directly between the IdP and **every AWS account** that requires integration.

*   **Use Case:** This pattern is generally considered viable for a non-multi-account environment or in niche scenarios where the design considerations of IAM Identity Center cannot be met.

## II. Machine-to-Machine (M2M) Identity Management

M2M authentication enables services and applications running inside or outside AWS to securely access resources using temporary credentials.

| Identity Type | Service/Mechanism | Details |
| :--- | :--- | :--- |
| **Workloads in AWS** | **EC2 Instance Profiles** | Recommended for applications running on EC2 instances. An IAM role is assigned to the instance profile, providing temporary security credentials for the application to access AWS APIs without using long-term access keys. |
| **Workloads outside AWS** | **IAM Roles Anywhere** | Extends IAM to grant access to non-AWS workloads (on-premises servers, other cloud providers) using temporary security credentials derived from **X.509 certificates**. This avoids the need for permanent AWS access keys. |
| **Customer Applications** | **Amazon Cognito Client Credentials Grant** | An OAuth-compliant flow where an application (App Client) authenticates directly with Amazon Cognito using a client ID and secret (without user context) to obtain a time-bound access token. This token is then used to access resources (Resource Server). |
| **API Access** | **Mutually Authenticated TLS (mTLS)** | Allows both the client and the server to authenticate each other using certificates with TLS before communicating, often supported by Amazon API Gateway and useful for high-regulation or IoT applications. |

## III. Customer Identity Management (CIAM)

**Amazon Cognito** is the primary service providing CIAM capabilities, adding user sign-up, sign-in, and access control to web and mobile applications.

*   **User Pools:** Serve as user directories, handling user registration, sign-in, and account recovery.

*   **Identity Pools:** Grant temporary **AWS credentials** to authenticated users, allowing them to access other AWS services.

*   **Federation:** Supports sign-in using social IdPs (Apple, Facebook, Google, Amazon) or enterprise IdPs through SAML 2.0 and OIDC.
