# Hybrid Cloud DNS Options for Amazon VPC

Hybrid Cloud DNS Architecture for Amazon VPC (Well-Architected)

This architecture provides seamless, bidirectional DNS resolution between your AWS environment (multiple VPCs/Accounts) and your on-premises data center. It is designed to be highly available, scalable, and cost-efficient, adhering to the AWS Well-Architected Framework by minimizing management overhead and infrastructure duplication.

## 1. Core Architectural Components

The "Well-Architected" pattern avoids creating DNS endpoints in every single VPC. Instead, it uses a **Centralized Shared Services Model**.

### Route 53 Resolver

The native DNS service available in every VPC (at VPC+2 address). This default resolver handles DNS queries within the VPC and can forward queries to custom resolvers based on resolver rules.

For detailed information on Route 53 Resolver, see [AWS Route 53 Resolver](./AWS_Route_53_Resolver.md).

### Shared Services VPC

A dedicated VPC (usually in a "Network" or "Shared Services" account) that hosts the resolver infrastructure. This centralizes DNS endpoint management and reduces costs.

### Inbound Endpoint

**Role:** Acts as the "Ear" for AWS. It listens for DNS queries coming from your on-premises servers (via Direct Connect/VPN).

**Function:** Resolves AWS private domains (e.g., `app.aws.corp` or Private Hosted Zones) for on-prem clients.

**Key Characteristics:**
- Deployed in the Shared Services VPC
- Listens on UDP/TCP port 53
- Receives queries from on-premises DNS servers
- Resolves AWS private hosted zones and VPC domain names

### Outbound Endpoint

**Role:** Acts as the "Mouth" for AWS. It speaks to your on-premises DNS servers.

**Function:** Forwards queries from AWS resources (e.g., EC2, Lambda) for on-prem domains (e.g., `db.corp.local`) to your on-prem DNS servers.

**Key Characteristics:**
- Deployed in the Shared Services VPC
- Forwards queries to on-premises DNS servers
- Uses resolver rules to determine which queries to forward

### Resolver Rules

Logic that tells Route 53: "If a query ends in `.corp.local`, send it to the Outbound Endpoint."

**Configuration:**
- Created once in the Shared Services account
- Defines domain patterns and target DNS server IPs
- Shared across all VPCs via AWS Resource Access Manager (RAM)

### AWS Resource Access Manager (RAM)

The "Glue" that shares the Resolver Rules with all other VPCs/Accounts, so they don't need their own Outbound Endpoints.

**Benefits:**
- Automatic propagation of DNS rules to new VPCs
- No manual configuration required per VPC
- Centralized management and updates

## 2. Hybrid DNS Query Flows

Hybrid DNS architecture manages two directional traffic flows over the private network connection:

| Flow Direction | Purpose & Mechanism | Example Workflow |
| :--- | :--- | :--- |
| **Outbound (VPC to On-Premises)** | To resolve domain names located on your private, on-premises network. | 1. An Amazon EC2 instance initiates a DNS query for an internal domain name (`internal.example.com`). 2. The query goes to the VPC Resolver. 3. A forwarding rule is configured to direct queries for this domain to an Outbound endpoint. 4. The endpoint sends the query to the on-premises DNS resolver via the private connection (DX or Site-to-Site VPN). |
| **Inbound (On-Premises to VPC)** | To resolve AWS resource names (e.g., EC2 instances or resources in a private hosted zone) from the external network. | 1. An on-premises client initiates a DNS query for an AWS resource domain (`dev.example.com`). 2. The on-premises DNS resolver forwards the query, based on a configuration rule, to an Inbound endpoint. 3. The query arrives at the inbound endpoint via the private connection. 4. The inbound endpoint sends the query to the VPC Resolver for resolution. |

## 3. Architecture Diagram & Traffic Flow

### Flow A: On-Premises Resolving AWS (Inbound)

1. **On-Prem Server** queries `app.aws.corp`.
2. **On-Prem DNS Server** has a conditional forwarder pointing `aws.corp` to the IPs of the AWS Inbound Endpoint (in Shared VPC).
3. **Query travels** over Direct Connect/VPN.
4. **Inbound Endpoint** receives query, checks Route 53 Private Hosted Zones, and returns the private IP of the AWS resource.

**Traffic Path:**
```
On-Prem Server → On-Prem DNS Server → Direct Connect/VPN → Inbound Endpoint (Shared VPC) → Route 53 Private Hosted Zone → Response
```

### Flow B: AWS Resolving On-Premises (Outbound)

1. **EC2 Instance** in a Spoke VPC queries `db.corp.local`.
2. **Route 53 Resolver** (local to Spoke VPC) checks its rules.
3. It finds a **Shared Resolver Rule** (shared via RAM) that says "Forward `.corp.local` to On-Prem IPs".
4. Query is routed to the **Outbound Endpoint** (in Shared VPC).
5. **Outbound Endpoint** forwards the query to the On-Prem DNS Server IPs via Direct Connect/VPN.

**Traffic Path:**
```
EC2 Instance (Spoke VPC) → Route 53 Resolver (VPC+2) → Resolver Rule → Outbound Endpoint (Shared VPC) → Direct Connect/VPN → On-Prem DNS Server → Response
```

## 4. Best Practices for Configuration

For simplified management and governance across complex AWS environments, best practices center on consistency and reliance on default services:

### Avoid Overriding Defaults

It is recommended not to override the default DNS server within your VPC using DHCP options. Overriding the default VPC Resolver leads to:
- Higher utilization of specified DNS servers
- Unnecessary cross-AZ traffic
- Increased latency
- Added costs

**Best Practice:** Use the default VPC Resolver (VPC+2 IP address) which is automatically available in every VPC. This provides:
- High availability (automatically distributed across AZs)
- Low latency (local to each subnet)
- No additional cost
- Automatic failover capabilities

### Use Route 53 Profiles for Consistency

To maintain a consistent DNS configuration across numerous VPCs in an organization, you can group settings—including private hosted zones, resolver rules, query logging, and DNS firewall rules—into a Route 53 Profile. This profile can be centrally shared via AWS Resource Access Manager (RAM) and associated with all necessary VPCs.

**Benefits:**
- **Centralized Management:** Define DNS configuration once and apply across all VPCs
- **Consistency:** Ensures all VPCs have the same DNS rules and settings
- **Automation:** New VPCs automatically inherit the profile configuration
- **Simplified Updates:** Update the profile once, changes propagate automatically

**Configuration Steps:**
1. Create Route 53 Profile in Shared Services account
2. Add resolver rules, private hosted zones, and DNS firewall rules to the profile
3. Share profile via AWS RAM with Organization or specific OUs
4. Associate profile with VPCs (can be done automatically for new VPCs)

## 5. Well-Architected Implementation Guide

### A. Reliability (Availability & Resilience)

#### Multi-AZ Endpoints

Always deploy your Inbound and Outbound Endpoints across at least two (preferably three) Availability Zones. This ensures that if one AZ fails, DNS resolution continues.

**Best Practice:**
- Deploy endpoints in at least 2 AZs for high availability
- Deploy in 3 AZs for maximum resilience
- Each endpoint in a different AZ provides redundancy

#### IP Addressing

Assign static IPs to your Inbound Endpoints so your on-prem DNS configuration doesn't need to change.

**Configuration:**
- Inbound Endpoints receive static IP addresses per AZ
- Configure these IPs as forwarders in your on-premises DNS servers
- Document IP addresses for change management

### B. Operational Excellence (Management)

#### Centralize Rules

Create Resolver Rules once in the Shared Services account.

**Process:**
1. Create resolver rules in the Shared Services VPC/Account
2. Define domain patterns (e.g., `*.corp.local`)
3. Specify target DNS server IPs (on-premises DNS servers)
4. Associate rules with the Outbound Endpoint

#### Share via RAM

Use AWS RAM to share these rules with your entire AWS Organization. When a new Spoke VPC is created, it automatically gets the rules and can resolve on-prem domains immediately without extra config.

**Benefits:**
- Automatic propagation to new VPCs
- Single source of truth for DNS rules
- Reduced operational overhead
- Consistent DNS configuration across all accounts

**Configuration Steps:**
1. Create resolver rule in Shared Services account
2. Share rule via AWS RAM with Organization or specific OUs
3. Enable auto-association for new VPCs
4. Verify rule propagation to spoke VPCs

### C. Security

#### Security Groups

Apply strict Security Groups to your endpoints.

**Inbound Endpoint SG:**
- Allow UDP/TCP port 53 only from your On-Premises CIDR range
- Deny all other traffic
- Example: `Allow 53 from 10.0.0.0/8` (on-prem CIDR)

**Outbound Endpoint SG:**
- Allow UDP/TCP port 53 outbound only to your On-Premises DNS Server IPs
- Deny all other outbound traffic
- Example: `Allow 53 to 10.0.1.10, 10.0.1.11` (on-prem DNS IPs)

**Best Practice:** Use least-privilege principles. Only allow DNS traffic (port 53) from/to specific IP addresses or CIDR ranges.

#### Query Logging

Enable Route 53 Resolver Query Logging to debug DNS issues and audit "who queried what".

**Use Cases:**
- Troubleshooting DNS resolution failures
- Security auditing and forensics
- Performance monitoring
- Compliance requirements

**Configuration:**
- Create CloudWatch Log Group for query logs
- Enable query logging on resolver endpoints
- Set appropriate log retention period
- Monitor logs for anomalies

### D. Cost Optimization

#### Avoid Duplication

Do not deploy endpoints in every Spoke VPC. Each endpoint costs ~$125/month/AZ. By centralizing in a Shared Services VPC and sharing rules, you pay for the endpoints once for the whole organization.

**Cost Comparison:**

| Approach | Endpoints | Cost (per month) |
| :--- | :--- | :--- |
| **Centralized (Recommended)** | 2 endpoints × 2 AZs = 4 ENIs | ~$500/month |
| **Distributed** | 10 VPCs × 2 AZs = 20 ENIs | ~$2,500/month |

**Savings:** Centralized approach saves ~$2,000/month for 10 VPCs.

**Additional Benefits:**
- Reduced management overhead
- Easier troubleshooting
- Consistent DNS configuration
- Simplified security policies

## 6. Summary Checklist

| Component | Configuration |
| :--- | :--- |
| **VPC Design** | Dedicated "Shared Services" VPC. |
| **Connectivity** | Transit Gateway or VPC Peering to connect Spokes to Shared VPC (for Outbound traffic path). |
| **Inbound** | 2+ ENIs in different AZs. IPs configured as Forwarders on On-Prem DNS. |
| **Outbound** | 2+ ENIs in different AZs. |
| **Rules** | Created in Shared Account, shared to Org via RAM. Auto-associate with new VPCs. |
| **On-Prem** | Update DNS servers to forward AWS zones to Inbound Endpoint IPs. |

## 7. Implementation Steps

### Step 1: Create Shared Services VPC

1. Create a dedicated VPC in the Network/Shared Services account
2. Create subnets in at least 2 Availability Zones
3. Ensure connectivity to spoke VPCs via Transit Gateway or VPC Peering

### Step 2: Deploy Inbound Endpoint

1. Navigate to Route 53 Resolver → Inbound Endpoints
2. Create endpoint with:
   - Name: `inbound-dns-endpoint`
   - VPC: Shared Services VPC
   - Subnets: Select subnets in 2+ AZs
   - Security Group: Allow UDP/TCP 53 from on-prem CIDR
3. Note the IP addresses assigned to each ENI
4. Configure on-premises DNS servers to forward `aws.corp` to these IPs

### Step 3: Deploy Outbound Endpoint

1. Navigate to Route 53 Resolver → Outbound Endpoints
2. Create endpoint with:
   - Name: `outbound-dns-endpoint`
   - VPC: Shared Services VPC
   - Subnets: Select subnets in 2+ AZs
   - Security Group: Allow UDP/TCP 53 to on-prem DNS IPs
3. Note the endpoint ID for resolver rule association

### Step 4: Create Resolver Rules

1. Navigate to Route 53 Resolver → Rules
2. Create rule:
   - Name: `forward-corp-local`
   - Rule Type: Forward
   - Domain: `corp.local` (or `*.corp.local`)
   - Target IPs: On-premises DNS server IPs
   - Associate with: Outbound Endpoint
3. Share rule via AWS RAM:
   - Select the resolver rule
   - Share with Organization or specific OUs
   - Enable auto-association with new VPCs

### Step 5: Configure On-Premises DNS

1. Add conditional forwarder for AWS domains:
   - Domain: `aws.corp` (or your AWS domain)
   - Forward to: Inbound Endpoint IP addresses
2. Test resolution from on-premises:
   - `nslookup app.aws.corp`
   - Should resolve to AWS private IP

### Step 6: Verify and Test

1. **Test AWS → On-Prem:**
   - From EC2 instance in spoke VPC: `nslookup db.corp.local`
   - Should resolve to on-premises IP

2. **Test On-Prem → AWS:**
   - From on-premises server: `nslookup app.aws.corp`
   - Should resolve to AWS private IP

3. **Enable Query Logging:**
   - Create CloudWatch Log Group
   - Enable logging on both endpoints
   - Monitor logs for issues

## Conclusion

This architecture ensures you have a robust, "set-it-and-forget-it" DNS fabric that scales effortlessly as you add more accounts and VPCs. By centralizing DNS endpoints in a Shared Services VPC and leveraging AWS Resource Access Manager, you achieve:

- **Cost Efficiency:** Pay for endpoints once, not per VPC
- **Operational Excellence:** Centralized management and automatic propagation
- **Reliability:** Multi-AZ deployment ensures high availability
- **Security:** Strict security groups and query logging for auditability
- **Scalability:** Automatically works for new VPCs without additional configuration

## References

- **[AWS Route 53 Resolver](./AWS_Route_53_Resolver.md)** - Detailed information on Route 53 Resolver functionality
- **[AWS Multi-VPC Network Infrastructure](./AWS_Multi_VPC_Network_Infrastructure.md)** - Multi-VPC architecture patterns including DNS
- **[AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md)** - Hybrid connectivity options including Direct Connect and VPN
