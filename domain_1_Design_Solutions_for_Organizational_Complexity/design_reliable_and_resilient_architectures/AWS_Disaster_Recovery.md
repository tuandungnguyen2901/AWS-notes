# AWS Disaster Recovery

Disaster recovery (DR) planning for workloads on AWS is a critical aspect of achieving overall workload resiliency, focusing on minimizing downtime (RTO) and data loss (RPO) following a disaster event. AWS Elastic Disaster Recovery (DRS) is the specialized service designed to achieve rapid, reliable recovery in the cloud for applications hosted on premises or in other cloud environments.

For detailed information on backup strategies and data replication techniques to meet RTO/RPO requirements, see [AWS Backup and Recovery Strategies](./AWS_Backup_and_Recovery_Strategies.md).

## I. Foundational Disaster Recovery Concepts

Disaster recovery is defined by preparing for and recovering from a disaster, which can include natural disasters, technical failures (like power failure), or human actions (such as misconfiguration or malicious attack).

### Recovery Objectives (RTO and RPO)

Organizations define recovery strategies based on two key objectives, determined through business impact analysis and risk assessment:

1. **Recovery Time Objective (RTO)**: The maximum acceptable delay between the interruption of service and the restoration of service. This defines the maximum acceptable downtime.

2. **Recovery Point Objective (RPO)**: The maximum acceptable amount of time since the last valid data recovery point. This defines the maximum acceptable data loss.

### DR vs. High Availability (HA)

While both concepts use similar best practices like monitoring and deploying to multiple locations, they differ in scope:

• **High Availability (HA)**: Focuses on components of the workload and maintaining continuous operability against common disruptions (e.g., component failures). HA architectures typically run workloads across multiple Availability Zones (AZs).

• **Disaster Recovery (DR)**: Focuses on discrete copies of the entire workload and addresses larger-scale, typically rarer, disaster events. DR often relies on deploying systems across multiple independent AWS Regions.

## II. Disaster Recovery Strategies in the Cloud

AWS outlines four main DR strategies, ranging in complexity and cost, tailored to meet different RTO and RPO targets:

| Strategy | RTO / RPO Target | Architectural Approach and Cost |
| :--- | :--- | :--- |
| **1. Backup and Restore** | Hours / Hours | Lowest priority use cases. Data is backed up (e.g., EBS snapshots, S3 replication) and stored in a recovery location. All infrastructure, configuration, and application code must be redeployed (provisioned) after the event, ideally using Infrastructure as Code (IaC). Cost: $. |
| **2. Pilot Light (used by DRS)** | RTO/RPO: Tens of Minutes / Seconds | Data replication is continuous, and core infrastructure (like databases and minimal resources) is "always on" or pre-provisioned. Other resources (application servers) are "switched off" (not deployed) and are provisioned only when failover is necessary. Cost: $$. |
| **3. Warm Standby** | RTO/RPO: Minutes | A scaled-down, fully functional mirror of the production environment is continuously running in the secondary location. Requires only scaling up resources after the event. Suitable for business-critical applications. Cost: $$$. |
| **4. Multi-site Active/Active** | RTO/RPO: Near Real-time / Real-time or Zero downtime | The workload runs simultaneously in multiple Regions, serving traffic from all sites (Hot Standby is a similar strategy but only one site actively serves traffic). Most complex and costly, suitable for mission-critical services. Cost: $$$$. |

**Data Replication Services (RPO focus)**: For low RPO targets in Pilot Light and Warm Standby, continuous cross-Region asynchronous data replication is used via services like Amazon S3 Replication, Amazon RDS read replicas, and Amazon Aurora global databases.

**Traffic Failover (RTO focus)**: Failover (traffic re-routing) is a network operation performed outside of DRS, often using Amazon Route 53 or AWS Global Accelerator. For manually initiated failover that uses highly available data plane APIs, Amazon Application Recovery Controller (ARC) with health checks can be used.

## III. AWS Elastic Disaster Recovery (DRS) Implementation

AWS Elastic Disaster Recovery (DRS) implements a Pilot Light strategy by continuously replicating data and maintaining minimal staged resources in the AWS cloud.

### 1. Initialization and Architecture

The DRS service must be initialized in the target AWS Region before use.

• **Replication Agent**: The AWS Replication Agent is installed on the source servers (physical, virtual, or cloud-based applications).

• **Staging Area Subnet**: A dedicated subnet is created in the target AWS VPC to serve as the staging area. This hosts Replication Servers (lightweight EC2 instances). For recovery into an AWS Local Zone, the staging area subnet should typically be set within the parent AWS Region to ensure optimal launch conditions.

• **Data Flow**: The agent performs continuous block-level replication of the underlying server disks, sending compressed and encrypted data to the Replication Servers. Each disk on the source server has an identically-sized EBS volume attached to a Replication Server in the staging area.

### 2. Network Requirements and Data Security

Connectivity is established over specific encrypted TCP ports:

| Port | Communication Direction | Purpose |
| :--- | :--- | :--- |
| **TCP Port 443** | Bidirectional: Source Servers ↔ DRS API Endpoint; Staging Area Subnet ↔ DRS API Endpoint | Used for Control Protocols (status updates, configuration, downloading the agent/replication software). All communication is secured using TLS. |
| **TCP Port 1500** | One-way: Source Servers → Staging Area Subnet | Used exclusively for continuous, compressed, and encrypted block-level data transfer. The inbound security group rule for the staging area must allow this traffic. |

• **Bandwidth**: The required bandwidth over TCP Port 1500 must be equal to or exceed the sum of the average write speed of all replicated source machines to avoid replication lag.

• **Data Encryption**: Replicated data is encrypted and compressed in transit over TCP Port 1500. The data is decrypted upon arrival at the staging area subnet and written to the EBS volumes.

### 3. Recovery and Failback

• **Recovery Instance Launch**: When a drill or recovery instance is launched, DRS automatically converts the disk format and injects drivers/cloud tools so the server can boot and run natively on AWS (a process that takes minutes).

• **Failover Execution**: Recovery instances are launched based on the configured launch settings and a chosen Point-in-Time (PIT) snapshot. If the workload uses an encrypted EBS volume with a Customer Managed Key (CMK), that key must be shared with the target account for recovery to succeed.

• **Failback to On-Premises**: Failback restores the recovered instances back to the source infrastructure. This is done by booting the Failback Client ISO on the target server (original or new). The Failback Client then communicates back to the AWS Recovery Instance over TCP Port 1500 to initiate reverse replication of the data. For performing large-scale failbacks to VMware vCenter, the DRS Mass Failback Automation Client (DRSFA Client) is used.

## IV. DR Operations and Best Practices

For a reliable and resilient architecture, consistent practices must be maintained.

• **Regular Drilling**: Non-disruptive recovery drills are integral and should be performed frequently (at least several times a year) to confirm that the recovery plan and applications work as expected in the recovery Region. Drills consume actual EC2 resources and must be manually terminated afterward to avoid charges.

• **Launch Protection**: When launching recovery instances for a real event, immediately enable Termination Protection after performing launch validation tests and before redirecting production traffic, to prevent accidental termination.

• **Avoiding Data Loss**: Do not use the Disconnect from AWS action on a source server during an active recovery event, as this action permanently terminates replication resources and the valuable Point-in-Time (PIT) snapshots.

• **Cross-Region Recovery**: DRS supports replicating EC2 instances across AWS Regions. The failover involves performing reverse replication from the recovered instance in Region 2 back to Region 1, creating a new Source Server (A2) in the original region.

• **Multi-Account Recovery**: For scaling beyond the 300 source server limit per account/Region or for organizational isolation, multiple staging accounts can be used. Source servers from staging accounts can be managed and recovered from a single target AWS account (extended source servers).
