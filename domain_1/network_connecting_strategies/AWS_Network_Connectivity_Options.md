# AWS Network Connectivity Options

AWS offers a comprehensive suite of network connectivity options designed to meet various performance, security, availability, and geographic requirements, including cloud-native, hybrid, and edge solutions.

## I. Connectivity via AWS Global Infrastructure and Proximity

AWS Global Infrastructure provides the foundation for connectivity, aiming for high performance and low latency worldwide.

• **Regions and Availability Zones (AZs)**: An AWS Region is a physical location globally where AWS clusters its data centers, isolated and independent from other Regions. An Availability Zone (AZ) consists of one or more discrete data centers within a Region, each having independent power, cooling, and networking. AZs within the same Region are physically separated (up to approximately 100 km) to prevent correlated failures but are connected via fully redundant, high-bandwidth, ultra-low-latency private networks, often achieving single-digit millisecond latency.

• **Global Network Backbone**: Every data center, AZ, and AWS Region is interconnected via a purpose-built, highly available, and low-latency private global network infrastructure. Traffic between AWS Regions travels over this backbone, not the public internet.

## II. Connectivity within or between Virtual Private Clouds (VPCs)

These options define how traffic is routed between private networks in the AWS Cloud:

• **Amazon Virtual Private Cloud (VPC)**: This is a logically isolated section of the AWS Cloud where resources are launched in a virtual network defined by the user.

• **VPC Peering**: A networking connection between two VPCs (which can be in different Regions or owned by different accounts) that enables resources in both VPCs to communicate using private IP addresses as if they were on the same network. VPC peering is neither a gateway nor a VPN connection and does not introduce a single point of failure or bandwidth bottleneck.

• **AWS Transit Gateway (TGW)**: This acts as a network transit hub, simplifying the interconnection of multiple VPCs and on-premises networks using a hub-and-spoke model. Transit Gateway can connect thousands of VPCs within the same AWS Region, eliminating the complexity of managing a mesh of multiple VPC peering connections.

• **AWS Cloud WAN**: This is an intent-driven managed wide area network (WAN) that unifies your data center, branch, and AWS networks through a policy you define. While you can create your own global network by interconnecting multiple Transit Gateways across Regions, Cloud WAN provides built-in automation, segmentation, and configuration management features designed specifically for building and operating global networks based on your core network policy. Cloud WAN features include automated VPC attachments, integrated performance monitoring, and centralized configuration. The core network policy is written in a declarative language that defines segments, AWS Region routing, and how attachments should map to segments, allowing you to describe your intent for access control and traffic routing while AWS Cloud WAN handles the network configuration details. Cloud WAN is managed within AWS Network Manager, which enables you to centrally manage and visualize your Cloud WAN core network and Transit Gateway networks across AWS accounts, Regions, and on-premises locations. Network Manager provides dashboard visualizations including world maps of network resources, 15 months of CloudWatch statistics, real-time event tracking, and topological/logical diagrams. Both Transit Gateway and Cloud WAN allow centralized connectivity between VPCs and on-premises locations: Transit Gateway is optimal for customers operating in a few AWS Regions who want to manage their own peering and routing configuration, while Cloud WAN is optimal for customers who want to define their global network through policy and have the service implement the underlying components automatically. Cloud WAN supports both IPv4 and IPv6, and Core Network Edge (CNE) inherits many Transit Gateway characteristics, such as throughput per VPC attachment. ([Reference](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/aws-cloud-wan.html))

• **[AWS PrivateLink / VPC Endpoints](./AWS_PrivateLink.md)**: This enables private connectivity between a VPC and supported AWS services, other VPCs, or endpoint services hosted by other accounts.
    ◦ **Interface Endpoints**: Provisions an Elastic Network Interface (ENI) with a private IP as an entry point; supports most AWS services.
    ◦ **Gateway Endpoints**: Provisions a gateway for private connectivity specifically to Amazon S3 and DynamoDB.

• **Software VPN (VPC-to-VPC)**: This describes connecting Amazon VPCs using VPN connections established between user-managed software VPN appliances running inside of each Amazon VPC. This provides flexibility for organizations that prefer to manage their own VPN infrastructure for inter-VPC connectivity.

• **Software VPN-to-AWS Site-to-Site VPN**: This describes connecting Amazon VPCs with a VPN connection established between a user-managed software VPN appliance in one Amazon VPC and AWS Site-to-Site VPN attached to the other Amazon VPC. This enables hybrid connectivity scenarios where one VPC uses managed AWS VPN and another uses a software VPN appliance.

• **Transit VPC**: This describes establishing a global transit network on AWS using a software VPN in conjunction with an AWS-managed VPN. A Transit VPC acts as a hub that connects multiple VPCs and on-premises networks, enabling global network connectivity across AWS Regions and customer networks.

## III. Hybrid Connectivity (On-premises to AWS)

These services establish secure links between customer-owned physical networks and the AWS Cloud:

• **AWS Direct Connect (DX)**: This service establishes a dedicated network connection from an on-premises location (data center, office) to AWS, bypassing internet service providers.
    ◦ **Private Virtual Interface (VIF)**: Used to access a VPC using private IP addresses.
    ◦ **Public Virtual Interface (VIF)**: Used to access all AWS public services globally using public IP addresses (e.g., Amazon S3).
    ◦ **Transit Virtual Interface (VIF)**: Used to access one or more AWS Transit Gateways.

• **AWS Site-to-Site VPN**: This establishes secure, encrypted tunnels (using IPSec) over the public internet between an on-premises network (Customer Gateway) and an AWS VPC/Transit Gateway. Each VPN connection is configured with two tunnels for high availability.

• **AWS Transit Gateway + AWS Site-to-Site VPN**: This combination establishes a managed IPsec VPN connection from your network equipment on a remote network to a regional network hub for Amazon VPCs, using AWS Transit Gateway. This enables centralized connectivity for multiple VPCs through a single VPN connection.

• **AWS Direct Connect + AWS Transit Gateway**: This combination establishes a private, logical connection from your remote network to a regional network hub for Amazon VPCs, using AWS Direct Connect and AWS Transit Gateway. This provides dedicated connectivity with centralized routing for multiple VPCs.

• **AWS Direct Connect + AWS Site-to-Site VPN**: This combination establishes a private, encrypted connection from your remote network to Amazon VPC, using Direct Connect as the primary path with AWS Site-to-Site VPN as a backup or for additional encryption. This provides redundancy and enhanced security.

• **AWS Direct Connect + AWS Transit Gateway + AWS Site-to-Site VPN**: This combination establishes a private, encrypted connection from your remote network to a regional network hub for Amazon VPCs, using Direct Connect and AWS Transit Gateway with Site-to-Site VPN for encryption. This provides dedicated connectivity, centralized routing, and encryption for multiple VPCs.

• **Site-to-Site VPN CloudHub**: This establishes a hub-and-spoke model for connecting remote branch offices. Multiple Customer Gateways can connect to a single Virtual Private Gateway, enabling branch-to-branch communication through AWS while maintaining a single VPN connection per branch.

• **Software VPN**: This establishes a VPN connection from your equipment on a remote network to a user-managed software VPN appliance running inside an Amazon VPC. This provides flexibility for organizations that prefer to manage their own VPN infrastructure using third-party or custom VPN solutions.

• **AWS Transit Gateway + SD-WAN solutions**: This describes the integration of software-defined wide area network (SD-WAN) solutions to interconnect several remote locations to a regional network hub for Amazon VPCs, using the AWS backbone or the internet as a transit network. This enables organizations to leverage their existing SD-WAN infrastructure while connecting to AWS.

## IV. Software Remote Access-to-Amazon VPC Connectivity

These options enable secure remote access for individual users and devices to resources within Amazon VPCs:

• **AWS Client VPN**: This is a managed client-based VPN service that enables you to securely connect users to AWS or on-premises networks using OpenVPN-based clients. AWS Client VPN provides secure access to resources in your VPCs from any location using an OpenVPN client, with support for authentication through Active Directory, mutual authentication, and network-based access control.

• **Software Client VPN**: This describes connecting software remote access to Amazon VPC, leveraging user-managed software VPN appliances. This provides flexibility for organizations that prefer to manage their own client VPN infrastructure using third-party or custom VPN solutions for remote user access.

## V. Specialized Low-Latency and Edge Connectivity

These solutions bring compute or content closer to the end user or device for optimal latency performance:

• **AWS Edge Locations and Amazon CloudFront**: Edge Locations are strategically positioned data centers (Points of Presence or PoPs) designed to optimize the delivery of content and applications by serving data from the location nearest to the end user. They work primarily with Amazon CloudFront, AWS's content delivery network (CDN), which caches frequently accessed content to reduce latency and server strain.

• **AWS Local Zones**: These extend an AWS Region to metropolitan areas, placing select AWS services (Compute, Storage, Database) close to end users. They are ideal for latency-sensitive applications requiring single-digit millisecond latency, like real-time gaming or media rendering.

• **AWS Wavelength Zones**: This solution embeds AWS compute and storage services (EC2, EBS, VPC) within the network edges of 5G telecommunications providers. Wavelength enables ultra-low latency (single-digit ms) applications by allowing traffic from 5G devices to reach application servers without leaving the telecom network.

• **AWS Outposts**: This brings native AWS services, infrastructure, and operating models to customer-owned physical sites (data centers, on-premises facilities). Outposts allow organizations to meet strict low latency (sub-millisecond) and data residency requirements locally while using the familiar AWS APIs and tools.

## VI. Networking Options in AWS Disaster Recovery (DR)

AWS Elastic Disaster Recovery (DRS) implements network strategies for failover and failback, especially between on-premises environments and the cloud:

• **Data Replication Traffic**: The AWS Replication Agent installed on source servers continuously replicates data to the staging area subnet in AWS. This block-level replication (compressed and encrypted) utilizes TCP port 1500 for data transfer to the replication servers.

• **Control Traffic**: Agent control protocols and status updates communicate over TCP port 443 with the AWS DRS regional API endpoints.

• **Connectivity Options for Replication**: Data replication can occur either over the public internet (using public IPs automatically assigned to replication servers) or through a private network connection (such as VPN, AWS Direct Connect, or VPC peering) if the "Use private IP" option is activated.

• **DRS Network Architecture**: Diagrams illustrate architectures for connectivity scenarios including: On-Premises to AWS, AWS Cloud to AWS Cloud via VPN, On-Premises to AWS Outposts, and On-Premises to AWS Local Zone.

## References

• [AWS VPC Connectivity Options Whitepaper - Introduction](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html)

