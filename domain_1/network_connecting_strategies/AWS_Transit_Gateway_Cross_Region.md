# Interconnecting Amazon VPCs Across AWS Regions Using Transit Gateway

Interconnecting Amazon Virtual Private Clouds (VPCs) across different AWS Regions using AWS Transit Gateway (TGW) establishes a highly scalable and reliable global network fabric over the AWS global infrastructure.

This guide details the architectural approach and key implementation concepts for setting up cross-Region VPC communication via Transit Gateway.

## I. Architectural Overview

AWS Transit Gateway is fundamentally a network transit hub or cloud router that interconnects VPCs and on-premises networks. By using inter-Region peering, you connect individual regional TGWs together, forming a global network that leverages the AWS Global Infrastructure.

### Regional Scope

TGW is a regional resource designed to connect thousands of VPCs within a single AWS Region using a hub-and-spoke model.

### Global Connection

Inter-Region peering allows TGWs located in different AWS Regions to exchange routing information, providing transitive connectivity across the global network.

### Data Transport

Network traffic traveling between AWS data centers via TGW peering connections stays entirely on the AWS Global Network Backbone and is automatically encrypted at the physical layer, ensuring data does not traverse the public internet.

**Key Benefits:**
- Traffic remains on AWS private network
- Automatic encryption at physical layer
- No public internet exposure
- Consistent performance and reliability

## II. Implementation Components and Configuration

To establish cross-Region VPC connectivity, you need to deploy and configure TGWs in each target Region and establish peering relationships.

### 1. Transit Gateway Deployment and VPC Attachment

#### Deploy TGW in Each Region

Create a Transit Gateway instance in each required AWS Region (e.g., Region A and Region B).

**Configuration Steps:**
1. Navigate to VPC Console → Transit Gateways
2. Create Transit Gateway in Region A
3. Create Transit Gateway in Region B
4. Configure appropriate settings (DNS support, default route table association, etc.)

#### Attach VPCs

In each Region, attach the local VPCs that need to participate in the global network to their respective regional TGW.

**Best Practice: Dedicated Subnets**

When deploying a TGW attachment in a VPC, ensure it resides in its own dedicated subnet and corresponding route table. This practice supports more complex routing configurations later on.

**Best Practice: Multi-AZ Deployment**

Deploy a TGW attachment in every Availability Zone (AZ) where resources need to communicate with the TGW, as traffic cannot route across AZs to reach a TGW attachment.

**Attachment Configuration:**
- Select VPC and subnets (one per AZ)
- Choose appropriate route table association
- Configure security groups if using appliance mode
- Enable DNS resolution if needed

#### Configure VPC Route Tables

The route tables within each VPC must be configured with static routes directing traffic destined for remote VPC CIDR blocks to the local TGW attachment.

**Example Route Configuration:**

| Destination | Target | Description |
| :--- | :--- | :--- |
| `10.1.0.0/16` | `tgw-attach-xxxxx` | Route to VPC in Region A |
| `10.2.0.0/16` | `tgw-attach-xxxxx` | Route to VPC in Region B |
| `0.0.0.0/0` | `igw-xxxxx` | Default route to Internet Gateway (if needed) |

### 2. Cross-Region Peering Setup

The connection between the two regional Transit Gateways (TGW A and TGW B) is established through a peering attachment.

#### Create Peering Attachment

Initiate a Transit Gateway peering attachment request from one TGW (e.g., TGW A) to the TGW in the destination Region (TGW B).

**Configuration Steps:**
1. Navigate to Transit Gateway → Peering Attachments
2. Create Peering Attachment
3. Select source Transit Gateway (TGW A)
4. Select peer Region and Transit Gateway (TGW B)
5. Configure peer account (if cross-account)
6. Submit peering request

#### Accept Request

The administrator of the destination TGW (TGW B) must accept the peering request.

**Acceptance Steps:**
1. Navigate to Transit Gateway → Peering Attachments
2. Locate pending peering request
3. Review peering details
4. Accept peering attachment
5. Verify status changes to "Available"

#### Configure TGW Route Tables for Peering

Once the peering connection is active, static routes must be added to the TGW route tables in both directions to enable traffic forwarding across the regions.

**TGW A's Route Table Configuration:**
- Add static route pointing to the peering attachment for all traffic destined for VPCs attached to TGW B
- Example: Route `10.2.0.0/16` → Peering Attachment to TGW B

**TGW B's Route Table Configuration:**
- Add static route pointing to the peering attachment for all traffic destined for VPCs attached to TGW A
- Example: Route `10.1.0.0/16` → Peering Attachment to TGW A

**Route Table Best Practices:**
- Use separate route tables for different environments (Production, Development)
- Associate VPC attachments with appropriate route tables
- Propagate routes from VPC attachments to enable dynamic routing
- Add static routes for cross-Region connectivity

### 3. Data Processing and Routing

#### Routing Decisions

A TGW determines the next hop for a packet based on the destination IP address defined in its route table. The target of these routes can be any other TGW attachment (VPC, VPN, or peering connection).

**Routing Process:**
1. Packet arrives at TGW from source attachment
2. TGW examines destination IP address
3. TGW consults route table for matching route
4. TGW forwards packet to target attachment
5. Packet continues to destination

#### Latency Awareness

While the traffic stays on the AWS backbone, you must be aware that cross-Region communication incurs higher latency compared to intra-Region traffic. Tools showing the infrastructure performance latency between Regions can help set appropriate application expectations.

**Latency Considerations:**
- Intra-Region: Typically < 1ms
- Cross-Region: Varies by distance (e.g., US-East-1 to EU-West-1: ~70-100ms)
- Use AWS Global Accelerator or Route 53 for latency-based routing
- Design applications to tolerate cross-Region latency
- Consider data replication strategies for latency-sensitive workloads

#### Maximum Transmission Unit (MTU)

A Transit Gateway supports an MTU of 8500 bytes for traffic between VPCs and across inter-Region peering attachments.

**MTU Considerations:**
- Standard Ethernet MTU: 1500 bytes
- Jumbo frames: Up to 8500 bytes
- Ensure all network components support jumbo frames if using larger MTU
- Test MTU discovery and path MTU discovery mechanisms

## III. Operational Considerations

### Cost

You are charged hourly for every attachment on a TGW, and separately for the amount of traffic processed by the TGW. Data processing charges are allocated to the account that owns the source attachment, although flexible cost allocation is available.

**Cost Components:**

| Component | Charge |
| :--- | :--- |
| **TGW Attachment** | ~$0.05 per hour per attachment |
| **Peering Attachment** | ~$0.05 per hour per peering |
| **Data Processing** | ~$0.02 per GB processed |
| **Cross-Region Data Transfer** | Additional charges apply |

**Cost Optimization:**
- Use Gateway Endpoints (S3, DynamoDB) instead of Interface Endpoints when possible
- Centralize shared services to reduce attachment count
- Monitor data transfer costs between Regions
- Use AWS Cost Explorer to analyze TGW costs

### Scale and Alternatives

TGW is optimal for customers who operate in a few AWS Regions and want to manage their own peering and routing configuration manually or with custom automation.

**When to Use Transit Gateway:**
- Few AWS Regions (< 5)
- Simple routing requirements
- Manual or custom automation preferred
- Hub-and-spoke topology sufficient

**When to Consider Cloud WAN:**

For environments requiring complex global segmentation policies or operating across many Regions, AWS Cloud WAN is the preferred service, as it uses a declarative Core Network Policy to manage complex routing automatically.

**Cloud WAN Advantages:**
- Declarative policy-based routing
- Automatic configuration management
- Built-in segmentation
- Simplified multi-Region operations
- Integrated monitoring and visualization

For more details on Cloud WAN, see [AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md).

### Resiliency

The TGW itself is inherently highly available. For connecting on-premises networks to this global infrastructure, Direct Connect or VPN connections should be used via a Transit Virtual Interface (VIF) connected to the TGW, typically requiring redundant connections across multiple physical locations for maximum SLA.

**High Availability Best Practices:**
- Deploy TGW attachments in multiple AZs
- Use redundant Direct Connect connections
- Configure multiple VPN tunnels
- Implement health checks and monitoring
- Design for automatic failover

**Disaster Recovery Considerations:**
- Replicate critical data across Regions
- Implement cross-Region backup strategies
- Test failover procedures regularly
- Document recovery procedures

### Encryption

All traffic between AWS data centers over the global backbone is automatically encrypted at the physical layer. Additionally, TGW supports an optional Encryption control feature to enforce encryption-in-transit for all attached VPC traffic.

**Encryption Options:**

1. **Physical Layer Encryption (Automatic)**
   - All traffic on AWS backbone is encrypted
   - No configuration required
   - Provides baseline security

2. **TGW Encryption Control (Optional)**
   - Enforces encryption-in-transit for VPC attachments
   - Can be enabled per attachment
   - Provides additional security layer

3. **Application-Level Encryption**
   - Use TLS/SSL for application traffic
   - End-to-end encryption
   - Application-specific security

**Security Best Practices:**
- Enable TGW encryption control for sensitive workloads
- Use security groups and NACLs for additional protection
- Implement VPC Flow Logs for monitoring
- Use AWS CloudTrail for audit logging
- Regular security assessments

## IV. Implementation Checklist

### Pre-Deployment

- [ ] Identify all Regions requiring connectivity
- [ ] Plan IP address ranges (avoid overlaps)
- [ ] Design route table structure
- [ ] Plan security groups and NACLs
- [ ] Estimate costs

### Deployment

- [ ] Create Transit Gateway in each Region
- [ ] Create VPC attachments in each Region
- [ ] Configure VPC route tables
- [ ] Create peering attachments
- [ ] Accept peering requests
- [ ] Configure TGW route tables
- [ ] Test connectivity

### Post-Deployment

- [ ] Enable monitoring and logging
- [ ] Configure CloudWatch alarms
- [ ] Document architecture
- [ ] Test failover scenarios
- [ ] Review costs and optimize

## V. Troubleshooting Common Issues

### Connectivity Issues

**Problem:** VPCs cannot communicate across Regions

**Solutions:**
- Verify peering attachment status is "Available"
- Check route tables in both TGWs have correct routes
- Verify VPC route tables point to TGW attachment
- Check security groups allow traffic
- Verify CIDR blocks don't overlap

### Performance Issues

**Problem:** High latency or packet loss

**Solutions:**
- Check Region-to-Region latency expectations
- Verify MTU settings are consistent
- Review CloudWatch metrics
- Check for network congestion
- Consider using Global Accelerator

### Cost Issues

**Problem:** Unexpected charges

**Solutions:**
- Review attachment counts
- Analyze data transfer volumes
- Check for unnecessary cross-Region traffic
- Optimize route table associations
- Use Cost Explorer for detailed analysis

## References

- **[AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md)** - Comprehensive connectivity strategies including Transit Gateway
- **[AWS Multi-VPC Network Infrastructure](./AWS_Multi_VPC_Network_Infrastructure.md)** - Multi-VPC architecture patterns
- **[AWS Well-Architected Networking Best Practices](./AWS_Well_Architected_Networking_Best_Practices.md)** - Best practices for networking architecture
- **[AWS Global Infrastructure](./AWS_Global_Infrastructure.md)** - Foundational infrastructure components
