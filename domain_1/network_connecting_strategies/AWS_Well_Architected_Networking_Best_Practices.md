# AWS Well-Architected Networking Best Practices

AWS networking encompasses practical approaches across infrastructure components, dedicated services for connectivity and traffic management, edge computing solutions, and tools for ensuring network security and resilience.

## I. Foundational Infrastructure Components

For detailed information on AWS foundational infrastructure components including Regions, Availability Zones, Edge Locations, Local Zones, Wavelength, and Outposts, see [AWS Global Infrastructure](./AWS_Global_Infrastructure.md).

## II. Core VPC Connectivity Strategies

For comprehensive details on VPC connectivity strategies including VPC Peering, Transit Gateway, Cloud WAN, PrivateLink/VPC Endpoints, Direct Connect, and Site-to-Site VPN, see [AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md).

For specific implementation details on PrivateLink and VPC Endpoints, see [AWS PrivateLink](./AWS_PrivateLink.md).

## III. Edge Computing Networking

For detailed information on edge computing networking solutions including Local Zones, Wavelength, and Outposts, see [AWS Global Infrastructure](./AWS_Global_Infrastructure.md) and [AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md).

## IV. Network Resilience and Security

Practical network design involves ensuring the architecture is highly available, secure, and prepared for disaster recovery.

### A. Network for Disaster Recovery (AWS Elastic Disaster Recovery - DRS)

For network architecture details on AWS Elastic Disaster Recovery (DRS) including ports, communication flows, and connectivity options, see [AWS Network Connectivity Options - Networking Options in AWS Disaster Recovery](./AWS_Network_Connectivity_Options.md#vi-networking-options-in-aws-disaster-recovery-dr).

### B. High Availability and Traffic Management

High availability architecture is achieved by removing single points of failure, typically by deploying across multiple Availability Zones.

#### Load Balancing

Traffic is distributed across targets using Elastic Load Balancing (ELB). Application Load Balancers (ALB) are used for HTTP/HTTPS (Layer 7) traffic, supporting microservices and containers, while Network Load Balancers (NLB) are best suited for high-performance TCP/UDP (Layer 4) traffic.

#### Global Traffic Steering

- **AWS Global Accelerator**: Uses static Anycast IP addresses at the AWS edge network to route user traffic to the closest healthy endpoint, providing fixed entry points and improving application availability and performance globally, especially for TCP/UDP use cases.
- **Amazon Route 53**: Provides various routing policies (like latency or geolocation) and is essential for implementing automatic failover based on health checks. See [Route 53 Resolver](./AWS_Route_53_Resolver.md) for DNS resolution within VPCs. For more details on Route 53 and Global Accelerator, see [AWS Global Infrastructure](./AWS_Global_Infrastructure.md).

### C. Network Security Services

AWS offers specialized services to protect the network boundary and the resources within the VPC.

#### Network Firewall (Layer 3-7)

A managed network firewall service for Amazon VPCs that allows deploying essential protections, including stateful inspection, intrusion prevention, and web filtering, and scales automatically with network traffic.

#### WAF (Layer 7)

A web application firewall protecting web applications and APIs (integrated with CloudFront, ALB, API Gateway, etc.) against common exploits like SQL injection and cross-site scripting.

#### Security Groups (SGs) and Network ACLs (NACLs)

- **Security Groups**: Operate at the instance/resource level and are stateful, allowing only specified inbound/outbound traffic.
- **Network ACLs**: Operate at the subnet level and are stateless, providing an additional layer of control over traffic flow.

#### Perimeter Management

- **AWS Firewall Manager**: Enables centralized configuration and management of WAF rules, Shield Advanced protections, and Network Firewall policies across multiple accounts in an AWS Organization, ensuring consistent security controls.
- **AWS Shield**: Provides managed DDoS protection (Standard for basic L3/L4 protection, Advanced for expanded L3, L4, and L7 protection).

## V. Implementation Best Practices

This section details implementation approaches and best practices across key areas of AWS networking, including foundational architecture, connectivity solutions, disaster recovery strategies, and governance.

### A. Foundational Architecture and Design Best Practices

Effective networking starts with designing the VPC structure to maximize performance and resilience while minimizing cross-dependency.

| Area | Implementation Details & Best Practices |
| :--- | :--- |
| **Availability Zone (AZ) Usage** | To achieve low latency, reduced risk, and lower cost, **minimize cross-AZ communication** where possible. Deploy critical applications and architecture components across a minimum of **two Availability Zones** (AZs) to ensure resilience against single-location failures. When setting up resources in a multi-account environment, use **AZ IDs** (e.g., `use1-az2`) rather than AZ names, as the latter can differ across accounts, maintaining consistency. |
| **VPC and Subnet Design** | When possible, define your system with **no single point of failure**. Prefer creating **private subnets** for hosting the majority of your workloads. Only place essential components, such as NAT Gateways or internet-facing load balancers, in public subnets. |
| **Internet Access Control** | Use **VPC Block Public Access** (VPA) for additional compliance and data plane control over connectivity to and from the internet. You can configure VPA to deny ingress traffic while still allowing outbound connectivity via a NAT Gateway. |
| **Load Balancing & Resilience** | Use Elastic Load Balancing (ELB) in conjunction with **Auto Scaling groups** to dynamically replace unhealthy instances and automatically distribute incoming traffic across multiple instances in different AZs. Utilize **Route 53 health checks** to monitor load balancer nodes and remove unhealthy nodes from DNS resolution. |

### B. Connectivity Implementation Strategies

For comprehensive connectivity options and their mechanisms, see [AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md). The following table provides implementation best practices for each connectivity type:

| Connectivity Type | Implementation Details & Best Practices |
| :--- | :--- |
| **VPC Peering** | Use peering connections for scenarios involving a **small number of VPCs** (maximum 125 peering links per VPC) that require the highest possible bandwidth and lowest latency, as this method essentially merges two VPCs. Remember that peering connections are **not transitive**; every pair of VPCs must have a direct connection if they need to communicate. |
| **AWS Transit Gateway (TGW)** | TGW is ideal for supporting hundreds or thousands of VPCs using a scalable hub-and-spoke design. Deploy the **TGW attachment in its own dedicated subnet** and corresponding route table within the VPC to allow for advanced networking options later. Ensure TGW attachments are placed in **every Availability Zone** where resources need to communicate with the TGW. |
| **AWS Cloud WAN** | Cloud WAN is recommended for defining global network segments using a declarative **Core Network Policy**. Leverage Cloud WAN segments to easily isolate groups of workloads (e.g., different research groups or environments). It can handle complex multi-region inspection scenarios and newly supports **AWS Direct Connect** termination directly onto the service. |
| **AWS Site-to-Site VPN** | When configuring the VPN connection, **configure both VPN tunnels** (Tunnel 1 and Tunnel 2) for inherent high availability. For full redundancy against device failure, complement this setup by having a separate set of tunnels configured to a distinct device on the customer side. |
| **AWS Direct Connect (DX)** | To consolidate connectivity from your on-premises network, use a **Transit Virtual Interface (VIF)** that connects to a centralized Transit Gateway, which is the preferred routing method for most customers. Most deployments only need **one Direct Connect Gateway** globally, as it is a control plane construct. Use **two connections in multiple locations** (maximum resiliency) for the highest Service Level Agreements (SLAs). |
| **VPC Endpoints (PrivateLink)** | Utilize **Gateway Endpoints** (free of charge) for connecting to S3 and DynamoDB. Use **Interface Endpoints** for accessing over 150 supported AWS services, other VPCs, or cross-region connections privately. These eliminate the need for NAT or Transit Gateway for communication to the target service. See [AWS PrivateLink](./AWS_PrivateLink.md) for detailed configuration guidance. |

### C. Disaster Recovery Implementation with Elastic Disaster Recovery (DRS)

Implementing AWS Elastic Disaster Recovery (DRS) requires careful configuration of network prerequisites and adherence to operational workflows to meet Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO).

#### A. Planning and Setup Best Practices

1. **Define Objectives:** Base your disaster recovery plan on a **Business Continuity Plan (BCP)**. Determine precise **RTO** (maximum downtime tolerance) and **RPO** (maximum data loss tolerance) objectives for your workloads based on business impact and the cost of recovery.

2. **Staging Area Subnet:** Create a **dedicated subnet** in the target AWS Region or VPC to serve as the staging area where Replication Servers are launched. This must be specified in the replication template.

3. **Local Zone Recovery:** If the recovery target is an AWS Local Zone, the best practice is to set the staging area subnet within the **parent AWS Region**, not the Local Zone, to ensure optimal launch conditions for replication and conversion servers.

4. **Security Measures:** When launching recovery instances for a real event, immediately enable **Termination Protection** after performing launch validation tests and before redirecting production traffic.

#### B. Network and Communication Requirements

DRS relies on two primary TCP ports for communication and data transfer:

| Port | Communication Flow | Purpose and Configuration |
| :--- | :--- | :--- |
| **TCP Port 443** | Bidirectional flow between **Source Servers** (running the Replication Agent) and the **DRS API endpoint** (`drs.<region>.amazonaws.com`). Also, flow between the **Staging Area Subnet** (Replication Servers) and the **DRS API endpoint**. | Used for control protocols, status updates, configuration, downloading software, and monitoring. All communication is encrypted using TLS. Firewalls must allow outbound TCP 443 access to the DRS regional API endpoints and required S3 buckets. |
| **TCP Port 1500** | Continuous, one-way flow from **Source Servers** to **Replication Servers** in the Staging Area Subnet. | Used solely for transferring the **compressed and encrypted block-level replication data**. The inbound rule in the Staging Area Security Group must allow traffic over this port. |
| **Bandwidth** | The required bandwidth over TCP Port 1500 must equal or exceed the **sum of the average write speed** of all replicated source machines to avoid lag. | Monitor the necessary write speed using tools like `iostat` (Linux) or DiskMon (Windows). |

#### C. Operational Best Practices

* **Drilling:** Perform **regular drills** (at least several times a year) to validate that applications function as expected in the recovery region and update the recovery plan with any findings. Drill instances utilize actual AWS resources and must be **terminated** after testing to avoid charges.

* **Active Recovery:** If a real disaster requires launching recovery instances, **do not use the `Disconnect from AWS` action** on the source server. Disconnecting terminates all replication resources, including the valuable Point-In-Time (PIT) recovery snapshots.

* **Failback Automation:** For performing large-scale failbacks to VMware vCenter, utilize the specialized **DRS Mass Failback Automation Client**.

### D. Security and Governance Implementation

Achieving a secure network requires implementing layered controls and centralized management across the entire organization.

| Strategy | Implementation Details & Best Practices |
| :--- | :--- |
| **Identity and Access** | Implement a **strong identity foundation** by adhering to the principle of **least privilege**. Use **AWS IAM Identity Center** (SSO) as the recommended service for workforce identity management to leverage temporary credentials instead of long-term IAM user access keys. Leverage **IAM Access Analyzer** to inspect resource policies and verify that public or cross-account access is not unintentionally granted. |
| **Network Segmentation (SGs/NACLs)** | Prefer using **Security Groups (SGs)** over Network ACLs (NACLs), as SGs are stateful and generally easier to manage. Use **SG cross-referencing** to allow communication between application tiers (e.g., web server layer to database layer) without relying on explicit IP addresses, simplifying management for dynamic environments. |
| **Traffic Inspection (Firewalls)** | For securing web applications, deploy **AWS WAF** (Layer 7 protection) and complement it with **AWS Shield** for DDoS mitigation. The recommended architecture for web applications is **distributed ingress**, where the firewall/WAF/CDN is deployed within each individual workload VPC/account, limiting the blast radius of any misconfiguration. |
| **Centralized Governance** | Utilize **AWS Organizations** to set security guardrails across multiple accounts. Implement **Service Control Policies (SCPs)** to define the **maximum permissions** allowed for IAM entities within member accounts. Deploy detective security services (like Amazon GuardDuty, AWS Security Hub CSPM, and AWS Config) across all accounts, often managing their findings centrally through a **Delegated Administrator account**. |
| **Logging and Auditing** | Enable an **organization trail** using **AWS CloudTrail** to log all API activity across all accounts, storing these logs immutably in a dedicated **Log Archive account**. Use **AWS Config** to continuously record resource configurations and automatically evaluate them against desired configurations. |

## References

For detailed information on specific networking topics covered in this best practices guide:

- **[AWS Global Infrastructure](./AWS_Global_Infrastructure.md)** - Foundational infrastructure components, Regions, Availability Zones, Edge Locations, Local Zones, Wavelength, and Outposts
- **[AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md)** - Comprehensive connectivity strategies including VPC Peering, Transit Gateway, Cloud WAN, Direct Connect, Site-to-Site VPN, and Disaster Recovery networking
- **[AWS PrivateLink](./AWS_PrivateLink.md)** - Detailed configuration and implementation guide for VPC Endpoints and PrivateLink
- **[AWS Route 53 Resolver](./AWS_Route_53_Resolver.md)** - DNS resolution within VPCs and hybrid DNS connectivity
- **[AWS Client VPN Configuration](./AWS_Client_VPN_Configuration.md)** - Remote access VPN solutions
