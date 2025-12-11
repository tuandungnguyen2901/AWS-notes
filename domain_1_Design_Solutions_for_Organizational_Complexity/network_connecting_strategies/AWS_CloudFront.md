# AWS CloudFront

AWS CloudFront is a crucial networking and content delivery service provided by AWS, functioning as a fast, serverless content delivery network (CDN) built for security and high performance. It is designed to securely and cost-effectively deliver data, videos, applications, and APIs globally with low latency and high transfer speeds.

## Core Functionality and Edge Infrastructure

CloudFront is integral to optimizing content delivery through the AWS global infrastructure:

• **Edge Locations**: CloudFront utilizes a global network of Edge Locations (or Points of Presence). An Edge Location is a site where CloudFront caches copies of your content to enable faster delivery by retrieving it from the point closest to the end user, thereby minimizing travel time.

• **Caching**: Content is cached at the nearest Edge Location. If requested content is not already cached, CloudFront retrieves it from the origin server (such as an Amazon S3 bucket or EC2 instance), caches it at the edge location, and then delivers it to the user. This operation helps reduce the load on origin servers and improves scalability, especially during periods of high traffic.

• **Content Types**: CloudFront supports the delivery of entire websites, including dynamic, static, streaming, and interactive content. It can be configured to route requests to multiple origins based on the content type, such as directing dynamic requests to an Elastic Load Balancer (ELB) and static content to Amazon S3.

## Security and Protection Features

CloudFront is integrated with several security services to create a layered perimeter:

• **DDoS Protection**: CloudFront provides inherent protection against common network layer and transport Distributed Denial of Service (DDoS) attempts. When used in conjunction with Amazon Route 53 and AWS Shield Standard, it provides comprehensive availability protection. Additionally, AWS Shield Advanced offers sophisticated DDoS protection for CloudFront distributions.

• **Web Application Firewall (WAF)**: AWS WAF can be integrated with CloudFront distributions, which means that the WAF rule processing occurs at the edge locations. This placement extends the security perimeter and filters malicious traffic closer to the source. The CloudFront security dashboard offers visibility and controls related to AWS WAF.

• **Encryption and Access**: You can enforce HTTPS communications between viewers and CloudFront using TLS certificates. This is often achieved by deploying public TLS certificates provided by AWS Certificate Manager (ACM). CloudFront can also restrict access to resources using signed URLs (for individual files) or signed cookies (for sitewide access to multiple files).

• **Origin Access Control (OAC)**: This feature restricts access to S3 origins, ensuring that content is only accessed through the intended CloudFront distribution and preventing direct public access. OAC replaces the older Origin Access Identity (OAI) feature and supports encryption with AWS Key Management Service (KMS).

## Architectural Considerations and Integrations

CloudFront is a critical component in network architecture design:

• **Edge Compute**: CloudFront works seamlessly with Lambda@Edge to run serverless functions at the edge, enabling real-time data processing and customization of content before it reaches the user.

• **Centralized Deployment**: In the AWS Security Reference Architecture, CloudFront distributions are often deployed centrally within the Network account. This centralized approach aids in easy control, configuration, and monitoring for all traffic flowing to the application.

• **Preventing Origin Bypass**: To ensure users do not bypass CloudFront and access the origin directly (e.g., an Application Load Balancer), CloudFront can be configured to add a custom HTTP header that the load balancer requires for forwarding the request. Alternatively, network access can be restricted by leveraging the CloudFront prefix list within the associated security group.

• **Global Networking**: CloudFront uses the AWS global network and edge locations. It is often compared to AWS Global Accelerator; while both improve performance globally, CloudFront is optimized for caching and content delivery, whereas Global Accelerator is recommended for non-HTTP traffic (like UDP/TCP for gaming or IoT) or when static IP addresses are needed.

• **Management**: You can quickly set up CloudFront using familiar AWS tools like the AWS Management Console, APIs, and AWS CloudFormation. AWS Config rules can be implemented to continuously monitor compliance, such as verifying that every CloudFront distribution is correctly associated with a Web ACL or configured to deliver access logs to an S3 bucket.
