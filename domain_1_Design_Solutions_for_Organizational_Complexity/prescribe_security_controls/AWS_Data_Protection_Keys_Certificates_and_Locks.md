# AWS Data Protection: Keys, Certificates, and Locks

AWS data protection relies on cryptographic tools and access controls, implemented through the use of keys, digital signatures, locks, and certificates, to maintain confidentiality, integrity, and controlled access.

## I. Cryptographic Keys and Key Management (AWS KMS)

AWS Key Management Service (AWS KMS) is a foundational service used to create and control cryptographic keys, providing security and resiliency by utilizing FIPS 140-2 Level 3 validated Hardware Security Modules (HSMs). KMS protects your root keys, and these keys never leave the service unencrypted.

For comprehensive details on AWS KMS implementation, key lifecycle management, access control, and advanced deployment patterns, see [AWS Key Management Service](./AWS_Key_Management_Service.md).

### A. Key Types and Ownership

1. **Customer Managed Keys (CMKs)**: These keys are created, owned, and managed by you in your AWS account. They are essential for protecting data in persistent storage like EBS, S3, and Aurora.

2. **AWS Managed Keys**: These are KMS keys in your account that are managed and used on your behalf by an integrated AWS service.

3. **AWS Owned Keys**: These keys are owned and managed by an AWS service for use across multiple accounts.

4. **Signing Keys**: KMS enables the control of keys used both for encrypting and signing your data.

### B. Encryption Usage and Management

• **Data at Rest Encryption**: AWS KMS is used to protect data at rest. New EBS volumes and snapshots can be encrypted by default across an AWS account and Region. Server-Side Encryption with KMS (SSE-KMS) can be applied to Amazon S3 objects, which adds a second layer of access control requiring both S3 read permissions and KMS decryption permissions.

• **Key Policies and Access Control**: You create and manage key policies in AWS KMS, ensuring that only trusted users have access to KMS keys. Key policies are the primary way to control access to keys, although IAM policies and grants can also be used.

• **Rotation**: AWS-managed KMS Keys automatically rotate every one year, while customer-managed KMS Keys can be configured for automatic or on-demand rotation.

• **Disaster Recovery (DRS)**: If EBS volumes are encrypted using a Customer Managed Key, that key must be shared with the target account to enable successful recovery of extended source servers into a separate target account.

• **External Key Stores (XKS)**: For customers with strict data sovereignty requirements, AWS KMS supports external key stores where the root encryption key is hosted in the customer's on-premises Hardware Security Module (HSM). The XKS proxy server acts as the intermediary between AWS KMS and the on-premises HSM.

## II. Certificates (TLS/SSL, ACM, and Private CA)

Certificates are central to securing data in transit and establishing trust, whether on the public internet or within private networks.

• **Transport Layer Security (TLS)**: All data flowing across the AWS global network is automatically encrypted at the physical layer before it leaves secured facilities. For public API endpoints, clients must support TLS 1.2 or later. Communication between the AWS Elastic Disaster Recovery (DRS) Replication Agent and the replication server is secured using TLS 1.2.

• **AWS Certificate Manager (ACM)**: ACM is the service used to provision, manage, import, and deploy public and private TLS certificates for use with integrated AWS services. It automatically handles certificate renewals for public certificates. ACM integrates seamlessly with Application Load Balancers (ALBs) and Amazon CloudFront distributions.

• **AWS Private Certificate Authority (Private CA)**: This managed service allows you to securely manage the lifecycle of private end-entity TLS certificates for internal resources like EC2 instances, containers, and IoT devices. Organizations can create a hierarchy (root CA through subordinate CAs) and issue certificates trusted only within their AWS organization, often managed centrally in a specialized security account and shared out using AWS Resource Access Manager (RAM).

## III. Signatures and Credentials

Digital signatures, often tied to temporary credentials, ensure the integrity and authenticity of requests.

• **Cryptographic Signing**: AWS KMS can be used to create and control cryptographic keys for signing data.

• **API Request Signing**: Requests made to AWS APIs must be signed using an Access Key ID and Secret Access Key associated with an IAM principal. Alternatively, requests can be signed using temporary security credentials (session tokens) obtained from the AWS Security Token Service (STS).

• **Replication Agent Authentication**: The continuous communication between the DRS Agent and the replication server is secured because requests are signed using an access key ID and a secret access key associated with an IAM principal. The process for generating temporary credentials for the agent relies on creating an X.509 certificate per agent and using this certificate to receive temporary IAM credentials (similar to IAM Roles Anywhere).

## IV. Data Locks (Immutability)

Data locks enforce immutability, primarily through Amazon S3 features, to protect data integrity against unintentional deletion or modification.

• **S3 Object Lock**: This feature is used to protect the integrity and availability of objects, such as logs, and is recommended for archiving security data like CloudTrail logs. It helps organizations meet regulatory requirements for Write Once, Read Many (WORM) storage.

• **Retention Modes**: S3 Object Lock supports Retention Governance mode (allowing specialized users to override locks) and Retention Compliance mode (preventing deletion by anyone, even the root user, for a set period).
