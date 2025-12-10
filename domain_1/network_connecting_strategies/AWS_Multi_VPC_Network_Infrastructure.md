# Building a Scalable and Secure Multi-VPC AWS Network Infrastructure

## 1. Abstract and Introduction

### The Foundational Concepts Required Before Deploying Resources

A scalable and secure multi-VPC AWS network infrastructure is architected upon the AWS Well-Architected Framework principles, focusing on organizational structure, core routing mechanisms, layered security controls, and robust disaster recovery strategies. This approach emphasizes defining explicit boundaries, automating governance, and ensuring resilience.

### The Problem

As you scale from one AWS account to hundreds, "Mesh" architectures (VPC Peering) break down due to complexity. The number of connections required follows the formula: $N \times (N-1) / 2$ connections, where N is the number of VPCs. This becomes unmanageable and costly at scale.

### The Solution

Adopt a **Hub-and-Spoke topology** for routing and a **Segmented approach** for security. This centralized model scales efficiently and simplifies management.

### IP Address Planning (Critical)

#### Avoid Overlap

You cannot route between overlapping CIDRs. Careful IP address planning is essential before deploying any VPCs.

#### Hierarchy

Assign CIDRs by hierarchy:
- **Region** → **Business Unit** → **Environment** (Prod/Dev)

Example structure:
- `10.0.0.0/16` - US-East-1 Production
- `10.1.0.0/16` - US-East-1 Development
- `10.10.0.0/16` - EU-West-1 Production
- `10.11.0.0/16` - EU-West-1 Development

#### IPv6

The whitepaper strongly suggests adopting IPv6 (/56 per VPC) to avoid the "IPv4 exhaustion" technical debt. IPv6 provides:
- Vast address space
- Simplified routing
- Native security features
- Future-proofing your architecture

### Multi-Account Strategy

A fundamental best practice for scaling network security is establishing a multi-account strategy governed by AWS Organizations. This strategy provides crucial boundaries for identity, access, and costs.

| Component | Purpose and Well-Architected Practice |
| :--- | :--- |
| **AWS Organizations (OUs)** | Used to centrally manage the environment, applying governance policies (guardrails) across all accounts. Group accounts by function (e.g., security, infrastructure, workloads) rather than mirroring corporate structure. |
| **Network Account (Infrastructure OU)** | Dedicated to managing network ingress (inbound), egress (outbound), and inspection traffic. This isolates core networking services and controls from individual workload accounts. |
| **Security Tooling Account** | Acts as the central administrative hub for detective and proactive security services, such as aggregating findings from AWS Security Hub CSPM and Amazon GuardDuty. |
| **Log Archive Account** | Dedicated for immutable storage of all security and operational logs (e.g., CloudTrail, VPC Flow Logs). |
| **Service Control Policies (SCPs)** | Enforced at the Organization/OU level, they define the maximum permissions available to users and roles within member accounts, acting as high-level guardrails. |

## 2. VPC to VPC Connectivity

How independent VPCs communicate within the AWS Cloud.

### VPC Peering

**Use Case:** High-bandwidth, low-latency, non-transitive connection between two specific VPCs (e.g., huge data transfer between Data Lake and Compute).

**Limitation:** Does not scale; hard to manage hundreds of peers. Maximum 125 peering links per VPC.

**Best Practice:** Use peering connections for scenarios involving a small number of VPCs that require the highest possible bandwidth and lowest latency. Remember that peering connections are **not transitive**; every pair of VPCs must have a direct connection if they need to communicate.

### AWS Transit Gateway (The Standard Hub)

**Architecture:** A regional router that acts as a hub. All VPCs attach here.

**Route Tables (VRFs):** You segment traffic by associating VPCs to different Route Tables (e.g., Prod, Dev, Shared). This allows you to control which VPCs can communicate with each other.

**Implementation Best Practices:**
- Deploy the TGW attachment in its own dedicated subnet and route table within the VPC. This is crucial for enabling future advanced networking options.
- Deploy a TGW attachment in every Availability Zone (AZ) used by the VPC, as traffic cannot route cross-AZ to the attachment.
- Use separate route tables for different environments (Production, Development, Shared Services) to enforce segmentation.

For more details, see [AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md).

### AWS PrivateLink

**Use Case:** One-way access to a specific service (not a whole network). Perfect for overlapping IPs (e.g., connecting a SaaS provider to your VPC).

**Implementation Best Practice:** Use Gateway Endpoints (for S3 and DynamoDB) whenever possible, as they are non-chargeable and simplify connectivity. Use Interface Endpoints for accessing over 150 supported AWS services, other VPCs, or cross-region connections privately.

For detailed configuration and implementation guidance, see [AWS PrivateLink](./AWS_PrivateLink.md).

### AWS Cloud WAN

**Use Case:** The modern evolution of Transit Gateway for Global networks.

**Mechanism:** Uses a Core Network Policy (JSON document) to enforce routing segments globally across all AWS Regions automatically. Cloud WAN automatically handles the underlying network configuration and is highly suitable for implementations requiring fine-grained isolation between large network segments.

**Implementation Best Practice:** Use multiple segments within Cloud WAN to isolate different groups of workloads (e.g., development, production, and inspection networks) based on policy rather than trying to force everything into one large segment.

### Amazon VPC Lattice

**New Layer:** Application-layer networking (Layer 7). Connects services (Kubernetes, Lambda) across VPCs without worrying about IP routing or overlapping CIDRs.

**Key Benefits:**
- Service-to-service connectivity without managing IP addresses
- Built-in authentication and authorization
- Traffic management and monitoring
- Works across VPCs, accounts, and AWS services

## 3. Hybrid Connectivity

Connecting on-premises infrastructure to AWS.

### AWS Site-to-Site VPN

**Use Case:** Quick setup, backup connectivity, or low throughput (< 1.25 Gbps).

**Implementation Best Practice:** Configure both VPN tunnels provided (Tunnel 1 and Tunnel 2) for inherent high availability. For maximum resilience, terminate the AWS VPN connection on your side using physically distinct devices.

**Accelerated VPN:** Uses AWS Global Accelerator to route traffic over the AWS backbone instead of the public internet for better stability. This improves performance and reduces latency compared to standard VPN connections.

### AWS Direct Connect (DX)

**Use Case:** Dedicated physical fiber. High throughput, consistent latency.

**Direct Connect Gateway:** The critical component that allows one physical fiber connection to access VPCs in any AWS Region (except China). This eliminates the need for multiple Direct Connect connections per region.

**Implementation Best Practice:** To meet high Service Level Agreements (SLAs), configure the network with two Direct Connect connections in multiple locations for redundancy. Use a Transit Virtual Interface (VIF) that connects to a centralized Transit Gateway for optimal routing.

**Encryption:** For strict compliance, use MACsec (Layer 2 encryption) over Direct Connect to encrypt data at wire speed. This provides encryption at the physical layer without impacting performance.

## 4. Centralized Egress to Internet

Allowing 100+ VPCs to access the internet without 100+ NAT Gateways.

### The Pattern: "Egress VPC"

**Architecture:**
1. Spoke VPCs send default traffic (`0.0.0.0/0`) to Transit Gateway.
2. Transit Gateway routes this to a dedicated Egress VPC.
3. NAT Gateway in the Egress VPC handles the internet access.

**Benefits:**
- Cost optimization: Single NAT Gateway instead of one per VPC
- Centralized security controls
- Simplified management and monitoring
- Consistent egress IP addresses

### Security Integration

**Network Firewall:** Insert AWS Network Firewall before the NAT Gateway to filter outbound traffic (e.g., "Allow yum.oracle.com, Block crypto-mining.com"). This provides centralized inspection and policy enforcement for all outbound internet traffic.

**IPv6 Egress:** Use Egress-Only Internet Gateways (EIGW) for IPv6 traffic, which naturally prevents inbound connections. This provides secure outbound-only connectivity for IPv6 resources.

## 5. Centralized Network Security (East-West)

Inspecting traffic moving between VPCs (e.g., Dev to Prod) or On-Prem to VPC.

### The Pattern: "Inspection VPC" (also called Security VPC)

### Gateway Load Balancer (GWLB)

The hero service for this pattern. It allows you to horizontally scale a fleet of firewalls (Palo Alto, Fortinet, etc.) behind a single endpoint.

**Traffic Flow:**
1. Source VPC → Transit Gateway
2. Transit Gateway → GWLB Endpoint (in Inspection VPC)
3. GWLB Endpoint → Firewall Appliance (Inspect/Block)
4. Firewall → GWLB Endpoint → Transit Gateway → Destination VPC

**Critical Config:** You MUST enable **Appliance Mode** on the Transit Gateway attachment for the Inspection VPC. If you miss this, return traffic will drop (asymmetric routing). Appliance Mode ensures that both forward and return traffic pass through the same firewall appliance.

**Benefits:**
- Centralized security policy enforcement
- Scalable firewall deployment
- Consistent inspection across all VPC-to-VPC traffic
- Integration with third-party security appliances

### AWS Network Firewall Alternative

A managed firewall service deployed in your VPCs (often an Inspection VPC) for stateful inspection, intrusion prevention, and web filtering. Provides Layer 3–7 protection at the VPC boundary and can be centrally managed across all accounts using AWS Firewall Manager.

## 6. Centralized Inbound Inspection (North-South)

Handling traffic coming IN from the internet to your applications.

### Option A: AWS Network Firewall

Deployed in the ingress path. Can decrypt TLS (if configured) and inspect payloads for SQL injection/XSS.

**Architecture:**
- Traffic hits Internet Gateway
- Route table redirects to Network Firewall endpoint
- Firewall inspects and filters traffic
- Forwarded to Application Load Balancer (ALB) or target resources

**Capabilities:**
- Stateful packet inspection
- Intrusion prevention system (IPS)
- Web filtering
- TLS decryption and inspection

### Option B: Gateway Load Balancer (Third-Party)

Allows you to use the same firewall appliances for Inbound, Outbound, and East-West traffic, unifying your security policy.

**Architecture:**
1. Traffic hits the Internet Gateway
2. Ingress Route Table redirects to Firewall Endpoint
3. Firewall inspects
4. Forwarded to Application Load Balancer (ALB)

**Benefits:**
- Unified security policy across all traffic directions
- Leverage existing firewall investments
- Consistent security controls
- Single pane of glass for security management

### Pattern Comparison

| Pattern | Mechanism | Security Benefit |
| :--- | :--- | :--- |
| **Distributed Ingress (Recommended)** | Internet-facing components (ALB, AWS WAF, CloudFront) are deployed directly within each workload VPC. | Limits the blast radius of any misconfiguration to a single workload and simplifies application-specific security management. |
| **Centralized Ingress (DMZ-like)** | Traffic is funneled through a single Network VPC housing the firewall layer. | Provides a single choke point for inspection, similar to on-premises design. |

### Additional Security Services

**AWS WAF:** A web application firewall that integrates with CloudFront and ALBs to protect against common application-layer exploits (Layer 7). Enables fine-grained filtering of web traffic based on content, headers, and known attack patterns.

**AWS Shield:** Provides managed Distributed Denial of Service (DDoS) protection at the edge. Shield Advanced offers specific mitigation rules and access to the DDoS Response Team (DRT). Essential for maintaining availability and performance during high-volume attacks.

## 7. DNS (Domain Name System)

Making On-Prem and Cloud resolve each other's hostnames.

For comprehensive guidance on implementing hybrid cloud DNS architecture with Route 53 Resolver endpoints, see [Hybrid Cloud DNS Options for Amazon VPC](./AWS_Hybrid_Cloud_DNS_Options.md).

### Route 53 Resolver Endpoints

#### Outbound Endpoint

Sits in a VPC and forwards queries for `corp.local` to your on-premise DNS servers.

**Use Case:** Allows resources in AWS VPCs to resolve on-premises hostnames.

#### Inbound Endpoint

Sits in a VPC and listens for queries from on-premise (via VPN/DX) to resolve `aws.internal`.

**Use Case:** Allows on-premises resources to resolve AWS VPC hostnames.

### Optimization

**Best Practice:** Do not deploy these in every VPC (expensive). Deploy them in a Shared Services VPC and share the resolving rules via AWS Resource Access Manager (RAM) to all other accounts.

**Route 53 Profiles:** Use Route 53 Profiles to centrally define and propagate consistent DNS configurations (private hosted zones, resolver rules) across every VPC in the organization.

### Default VPC Resolver

Use the default VPC Resolver (VPC+2 IP address) for high availability and scalability. This is automatically available in every VPC and provides DNS resolution for AWS services and public domains.

For detailed information on Route 53 Resolver functionality, see [AWS Route 53 Resolver](./AWS_Route_53_Resolver.md).

## 8. Centralized Access to VPC Private Endpoints

Accessing AWS Services (S3, SQS) privately.

### Interface VPC Endpoints (PrivateLink)

Instead of traversing the public internet to reach S3, traffic stays on the AWS private network. This provides:
- Enhanced security (no internet exposure)
- Improved performance (AWS backbone)
- Cost savings (no NAT Gateway required)
- Compliance benefits (private connectivity)

### Centralization Options

#### Option 1: Deploy Endpoints in Every Spoke VPC

**Pros:** Easiest to implement, no routing complexity
**Cons:** Costly (endpoint charges per AZ)

#### Option 2: Deploy Endpoints in Shared Services VPC

**Pros:** Cost-effective, centralized management
**Cons:** Complex routing via Transit Gateway

**Architecture:**
1. Spoke VPCs route traffic to Transit Gateway
2. Transit Gateway routes to Shared Services VPC
3. Shared Services VPC contains the Interface Endpoints
4. Traffic reaches AWS services privately

### DNS Handling

Use Private Hosted Zones to override public AWS DNS names (e.g., `s3.us-east-1.amazonaws.com`) to resolve to your private endpoint IPs. This ensures that:
- Applications continue using standard AWS service endpoints
- Traffic automatically routes to private endpoints
- No application code changes required

**Implementation:** Create a private hosted zone matching the AWS service endpoint domain name and create A records pointing to the Interface Endpoint IP addresses.

For detailed configuration guidance, see [AWS PrivateLink](./AWS_PrivateLink.md).

## 9. Conclusion

The whitepaper concludes that while you can start small, you must design for the Hub-and-Spoke model from Day 1. The cost of migrating from a mesh network to a centralized Transit Gateway architecture later is significantly higher than implementing it correctly at the start.

### Key Takeaways

1. **Start with Hub-and-Spoke:** Design your network architecture around Transit Gateway or Cloud WAN from the beginning, even if you only have a few VPCs initially.

2. **Plan IP Addresses Carefully:** Avoid CIDR overlaps and adopt IPv6 to future-proof your architecture.

3. **Centralize Security:** Use Inspection VPCs and centralized egress patterns to reduce costs and simplify security management.

4. **Optimize DNS:** Deploy Route 53 Resolver endpoints in Shared Services VPCs and share them via RAM to reduce costs.

5. **Centralize Endpoints:** Consider deploying Interface VPC Endpoints in a Shared Services VPC for cost optimization, especially at scale.

6. **Multi-Account Strategy:** Implement AWS Organizations with proper account separation (Network, Security, Log Archive) from the start.

### References

For additional implementation guidance and best practices:

- **[AWS Well-Architected Networking Best Practices](./AWS_Well_Architected_Networking_Best_Practices.md)** - Comprehensive best practices for networking architecture
- **[AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md)** - Detailed connectivity strategies and options
- **[AWS Global Infrastructure](./AWS_Global_Infrastructure.md)** - Foundational infrastructure components
- **[AWS PrivateLink](./AWS_PrivateLink.md)** - VPC Endpoints and private connectivity
- **[AWS Route 53 Resolver](./AWS_Route_53_Resolver.md)** - DNS resolution and hybrid DNS
- **[Hybrid Cloud DNS Options for Amazon VPC](./AWS_Hybrid_Cloud_DNS_Options.md)** - Well-architected hybrid DNS architecture implementation
