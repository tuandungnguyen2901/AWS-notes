# AWS Client VPN Configuration

AWS Client VPN is defined as one of the services that comprise AWS Virtual Private Network (Site-to-Site VPN) solutions, designed to establish secure connections for client devices to access AWS or on-premises resources using a VPN software client. It functions as a highly-available, managed, and elastic cloud VPN solution for managing remote access. It uses public IPv4 addresses for connectivity.

## Foundational Knowledge for AWS Client VPN Operations

Although the specific steps for configuring and deploying AWS Client VPN are not detailed in the provided materials, successful deployment requires fundamental knowledge in related AWS networking and security concepts:

1. **Network Connectivity Strategies**: Understanding networking concepts is essential, particularly those involving Amazon Virtual Private Cloud (Amazon VPC), VPNs, and potentially connecting to on-premises environments via services like AWS Direct Connect or Transit Gateway.

2. **Hybrid Connectivity**: Knowledge of evaluating connectivity options for integrating cloud resources with on-premises or co-location environments is necessary, as Client VPN facilitates this remote access.

3. **Security Controls**: Deploying a VPN solution requires knowledge of Identity and Access Management (IAM) and setting appropriate security controls. Client VPN is integrated with the suite of security services available on AWS.

## Context on AWS VPN Services

AWS Client VPN is deployed as part of the overarching AWS Virtual Private Network (VPN) solutions, which establish secure connections between your networks and the AWS global network.

• **AWS Client VPN** handles remote access for users.

• **AWS Site-to-Site VPN** creates encrypted tunnels between your network and your Amazon VPCs or AWS Transit Gateways.

Both of these VPN solutions establish encrypted network connectivity to a VPC over the internet using IPSec. If you require larger bandwidth, certain VPN configurations attached to Transit Gateway or AWS Cloud WAN can support up to 5 Gbps bandwidth per tunnel, compared to the standard 1.25 Gbps.

AWS Client VPN relies on VPC components like a route table to direct network traffic. Since the goal of a VPN solution is to allow private communication, you can leverage Amazon VPC endpoints for private connectivity to supported AWS services without using the public internet.

## Related Resources

• [AWS Network Connectivity Options](./AWS_Network_Connectivity_Options.md) - Overview of all AWS connectivity options including AWS Client VPN

