# AWS Network Security Architecture and Components

The following technical notes detail the architectural components, service capabilities, deployment models, and configuration techniques for building a secure AWS network infrastructure, aligning with the AWS Security Reference Architecture (AWS SRA) methodology.

## 1. Perimeter & Edge Protection (Shield Layer)

### Service

### Technical Capabilities and Configuration

**AWS Shield Standard**

Provides defense against the most common network (Layer 3) and transport (Layer 4) DDoS attacks. This protection is automatically included at no additional charge for all AWS customers utilizing AWS services like CloudFront, Route 53, and Elastic Load Balancing (ELB).

**AWS Shield Advanced**

Offers more sophisticated automatic mitigations for large, sophisticated DDoS attacks. It is applied to protected resources including EC2, ELB, CloudFront, Global Accelerator, and Route 53 hosted zones. Advanced features include 24x7 access to the AWS Shield Response Team (SRT) and protection against DDoS related cost spikes in resource charges.

**AWS WAF**

Functions as a web application firewall to protect web applications and APIs against common web exploits like SQL injection or Cross-Site Scripting (XSS). Rules are defined in Web Access Control Lists (ACLs) and can filter traffic based on IP addresses, HTTP headers/body, or URI strings. Customers can write custom rules or use Managed Rule Groups curated by AWS and its partners. AWS WAF supports integration with CloudFront, Application Load Balancer (ALB), and API Gateway.

**Amazon CloudFront**

Functions as a Content Delivery Network (CDN) service that provides inherent protection against common network and transport DDoS attempts. By routing traffic through a global network of Edge Locations, it filters malicious traffic close to the end-user. CloudFront delivers content using HTTPS and the latest TLS versions. Content access can be restricted using security features like signed URLs and signed cookies.

## 2. VPC Traffic Control (Filter Layer)

### A. Network Filtering Mechanisms

• **Security Groups (SGs)**: SGs operate as stateful firewalls at the instance/resource level (e.g., EC2 instances, load balancers, RDS). Because they are stateful, if inbound traffic is allowed, the corresponding return traffic is automatically permitted. SGs support allow rules only.

• **Network ACLs (NACLs)**: NACLs operate at the subnet level and are stateless. This means that both incoming traffic and the necessary return traffic must be explicitly allowed via separate rules. NACLs support both allow and deny rules, evaluated by rule number precedence. Best Practice: Due to the complexity of managing stateless connections (particularly ephemeral port ranges), security groups are generally favored over NACLs.

### B. VPC Endpoints for Private Connectivity

VPC Endpoints (powered by AWS PrivateLink) allow connecting VPCs to supported AWS services privately, ensuring traffic remains within the AWS network and avoids the public internet.

• **Gateway Endpoints**: These provision a gateway and require configuration in the VPC route table. They only support connectivity to Amazon S3 and Amazon DynamoDB. A significant advantage is that Gateway Endpoints are non-chargeable.

• **Interface Endpoints (PrivateLink)**: These deploy an Elastic Network Interface (ENI) with private IP addresses in your VPC subnets. They support over 150 AWS services and facilitate cross-VPC communication, supporting traffic to different accounts and even cross-regionally. Interface Endpoints incur charges for usage.

• **Configuration Detail**: VPC Endpoint Policies, which are IAM resource policies, can be attached to the endpoint to add an additional layer of control over which AWS principals can communicate with the services.

## 3. Network Inspection & Segmentation (Scanner Layer)

### Service

### Technical Capabilities and Deployment Details

**AWS Network Firewall**

This is a fully managed network firewall service for VPCs providing Layer 3 through Layer 7 protection. Capabilities include stateful inspection, intrusion prevention and detection (IPS), and web filtering. It supports importing Suricata rulesets. It is deployed on a per-Availability Zone basis in a dedicated firewall subnet.

**Gateway Load Balancer (GWLB)**

Operates at Layer 3 (IP packets) using the Geneve protocol (port 6081) to ensure transparent insertion of third-party network virtual appliances (such as Palo Alto, Check Point, Fortinet). The GWLB distributes traffic to a fleet of these appliances and manages their scaling.

### Inspection Architecture

For centralized inspection, an Inspection VPC is deployed to house the Network Firewall or GWLB endpoints. This enables filtering for East-West (VPC-to-VPC) traffic and North-South (ingress/egress to the internet/on-premises) traffic. The firewall subnet should be kept dedicated, as the firewall cannot inspect traffic originating from or destined for the same subnet it resides in.

## 4. Monitoring & Visibility (Camera Layer)

### Service

### Technical Functionality and Use

**VPC Flow Logs**

Captures IP traffic metadata (source/destination IPs, ports, protocols, bytes transferred, and ALLOW/DENY action) moving through network interfaces. Logs can be published to Amazon S3 or Amazon CloudWatch Logs. Used for network troubleshooting and reviewing security group or NACL evaluation.

**VPC Traffic Mirroring**

Enables security teams to copy (mirror) raw network packets from a source Elastic Network Interface (ENI) and route them to a target monitoring appliance (ENI or NLB). This technique provides packet-level forensics, including access to the actual payload content, supplementing the header information captured by Flow Logs.

**Amazon GuardDuty**

A threat detection service that continuously uses machine learning (ML) and threat intelligence to identify anomalous behavior and malicious activity, such as port scans, brute force attempts, and data exfiltration. It analyzes CloudTrail event logs, VPC Flow Logs, and DNS logs. GuardDuty operates through a delegated administrator model in AWS Organizations for centralized management (e.g., Security Tooling account). Findings are automatically sent to AWS Security Hub CSPM.

## Key Architectural Patterns & Takeaways

• **Zero Trust / Secure-by-Design Principles:**

    ◦ **Defense-in-Depth (DiD)**: Requires implementing multiple, layered security controls (preventive and detective) across all layers of the architecture (edge, network, application, instance).

    ◦ **Strong Identity Foundation**: Enforce the principle of least privilege and use temporary credentials (IAM roles, IAM Identity Center) instead of static long-term credentials.

    ◦ **Service Integration**: AWS Verified Access enforces ZT access by evaluating identity and device posture in real time for application access without relying on VPNs.

• **Hub & Spoke Model using AWS Transit Gateway for Centralized Network Inspection:**

    ◦ The Transit Gateway (TGW) establishes a highly scalable hub-and-spoke topology to connect thousands of VPCs and hybrid networks.

    ◦ Centralized inspection is achieved by routing all traffic through a dedicated Inspection VPC attached to the TGW. This approach simplifies management compared to point-to-point peering.

• **Security VPC Configuration (Inspection VPC):**

    ◦ A dedicated VPC isolates network inspection services, hosting AWS Network Firewall endpoints or Gateway Load Balancer (GWLB) interfaces to insert third-party security appliances.

    ◦ The GWLB enables transparent insertion of these firewalls to inspect East-West (VPC to VPC) and North-South (Internet Ingress/Egress) traffic.

• **DDoS-Resilient Architectures:**

    ◦ Resilience is achieved through layering: CloudFront and AWS Shield provide the first line of defense at the edge.

    ◦ Traffic is distributed using ALB or NLB across multiple Availability Zones (AZs).

    ◦ Auto Scaling groups ensure application availability and scalability by monitoring health checks and automatically replacing unhealthy instances to cope with high traffic load.
