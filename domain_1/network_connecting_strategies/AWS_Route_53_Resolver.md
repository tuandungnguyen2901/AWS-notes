# AWS Route 53 Resolver (VPC Resolver)

Amazon Route 53 Resolver, currently also referred to as VPC Resolver, is a key component for Domain Name System (DNS) resolution within the AWS Cloud, enabling connectivity for AWS resources and integration with on-premises networks.

## Core Functionality and Architecture

The Route 53 Resolver system is available by default in all Amazon Virtual Private Clouds (VPCs). Its fundamental role is to respond recursively to DNS queries originating from AWS resources. Specifically, it automatically resolves:

*   DNS queries for **public records** against public name servers on the internet.

*   Queries for **local VPC domain names** used by EC2 instances.

*   Queries for records within **Amazon Route 53 private hosted zones**.

The physical infrastructure supporting Route 53, a DNS service, relies on AWS Edge Locations to deliver low latency access. Within a VPC, the Resolver is accessed via a VPC+2 IP address within an Availability Zone.

## Hybrid DNS Resolution and Connectivity

Route 53 Resolver facilitates the creation of a hybrid cloud setup by enabling DNS queries between your VPCs and your on-premises resources, typically over AWS Site-to-Site VPN or AWS Direct Connect (DX). This hybrid DNS resolution relies on two main components: Resolver endpoints and conditional forwarding rules (Resolver rules).

| Endpoint Type | Function | Communication Path |
| :--- | :--- | :--- |
| **Inbound Resolver Endpoint** | Allows DNS queries **to** your VPC from an on-premises network or another VPC. | On-premises clients query the on-premises DNS resolver, which forwards the query to the inbound endpoint via a private connection (VPN/DX). The inbound endpoint sends the query to the VPC Resolver for resolution. |
| **Outbound Resolver Endpoint** | Allows DNS queries **from** your VPC to resolvers on your on-premises network or another VPC. | EC2 instances send queries to the VPC Resolver, which forwards the query to the outbound endpoint based on conditional forwarding rules. The outbound endpoint then forwards the query through a private connection to the on-premises DNS resolver. |

### Resolver Rules

Resolver rules are crucial for conditionally forwarding queries to the appropriate resolver. You create one forwarding rule for each domain name, specifying the domain for which queries should be forwarded and the IP addresses of the destination DNS resolvers on the on-premises network. These rules are applied directly to the VPC and can be shared across multiple accounts.

## Security with Route 53 Resolver DNS Firewall

The Route 53 Resolver DNS Firewall is a network protection service designed to safeguard web applications by filtering outbound DNS requests from your VPCs.

### Key Security Objectives:

*   **Preventing Data Exfiltration:** Its primary use is to help prevent DNS exfiltration of data.

*   **Access Control:** It allows you to monitor and control which domains your applications can query. You can set rules to either deny access to known malicious domains or implement strict security by denying all domains except those explicitly trusted.

*   **Blocking Resolution Requests:** The DNS Firewall can block resolution requests for specific resources, including private hosted zones, VPC endpoint names, or public/private EC2 instance names.

### Management and Integration

Management of DNS Firewall policies can be centralized using AWS Firewall Manager. Firewall Manager allows you to configure and manage Route 53 Resolver DNS Firewall rules across accounts and VPCs throughout your organization. This specialized firewall can be used alongside the AWS Network Firewall, where the DNS Firewall focuses on DNS query filtering and the Network Firewall focuses on network-layer and application-layer traffic filtering.

## Naming Context

The service was previously known simply as Route 53 Resolver, but the name was updated to **VPC Resolver** following the introduction of Route 53 Global Resolver. Understanding these hybrid DNS concepts, including the functions of the VPC Resolver and on-premises DNS integration, is a necessary area of knowledge for designing network connectivity strategies, as covered in the AWS Certified Solutions Architect - Professional exam.
