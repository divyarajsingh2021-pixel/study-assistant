"""
Script to generate 5 additional diverse sample PDFs for the RAG benchmark corpus.
All generated documents are authored explicitly for this open-source project and released under CC-BY 4.0 / Public Domain.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DOCS_DIR = Path(__file__).resolve().parent.parent / "sample_docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Title"],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#1e293b"),
    alignment=0,
    spaceAfter=10,
)
h1_style = ParagraphStyle(
    "DocH1",
    parent=styles["Heading1"],
    fontSize=14,
    leading=18,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=12,
    spaceAfter=6,
)
h2_style = ParagraphStyle(
    "DocH2",
    parent=styles["Heading2"],
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#334155"),
    spaceBefore=8,
    spaceAfter=4,
)
body_style = ParagraphStyle(
    "DocBody",
    parent=styles["BodyText"],
    fontSize=9.5,
    leading=14,
    textColor=colors.HexColor("#334155"),
    spaceAfter=6,
)
meta_style = ParagraphStyle(
    "DocMeta",
    parent=styles["Italic"],
    fontSize=8.5,
    leading=11,
    textColor=colors.HexColor("#64748b"),
    spaceAfter=12,
)


def generate_distributed_systems_pdf():
    pdf_path = DOCS_DIR / "Distributed_Systems_Consensus.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40
    )
    story = []

    # Page 1
    story.append(
        Paragraph("Distributed Systems: Consensus, Fault Tolerance & Replication", title_style)
    )
    story.append(
        Paragraph(
            "Course: CS402 Distributed Systems Architecture | License: CC-BY 4.0 Open Educational Resource",
            meta_style,
        )
    )
    story.append(Paragraph("1. Fundamentals of Distributed Computing and System Models", h1_style))
    story.append(
        Paragraph(
            "A distributed system consists of autonomous computing entities (nodes) that communicate over a network by exchanging messages without shared physical memory or a global physical clock. "
            "System models categorize distributed environments into synchronous, asynchronous, and partially synchronous. "
            "In a synchronous model, there is a known upper bound on message propagation delay and relative processor speeds. "
            "In contrast, the asynchronous model makes no timing assumptions: message delays are unbounded, and processor execution rates are arbitrary.",
            body_style,
        )
    )
    story.append(Paragraph("2. Time, Causality, and Vector Clocks", h1_style))
    story.append(
        Paragraph(
            "Because physical clocks drift due to quartz crystal imperfection, Leslie Lamport introduced logical clocks to define a partial ordering of events based on the 'happened-before' relation (denoted by ->). "
            "If event a occurs before event b in the same process, then a -> b. If a is the sending of a message and b is its receipt, then a -> b. "
            "However, Lamport timestamps cannot detect causal independence: if L(a) < L(b), it does not necessarily mean that a causally preceded b. "
            "Vector clocks resolve this limitation by maintaining a vector of logical timestamps representing each node's local view of progress. "
            "Event a causally preceded event b if and only if V(a)[k] <= V(b)[k] for all k and V(a)[i] < V(b)[i] for at least one index i.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("3. Distributed Consensus: Paxos and Raft", h1_style))
    story.append(
        Paragraph(
            "The consensus problem requires a set of nodes to agree on a single value or state machine transition despite node crashes and message drops. "
            "The FLP Impossibility Theorem (Fischer, Lynch, and Paterson, 1985) proved that deterministic asynchronous consensus is impossible if even a single node can suffer an unannounced fail-stop crash. "
            "Practical consensus algorithms therefore assume partial synchrony or randomized failure detectors.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Paxos, developed by Leslie Lamport, achieves consensus through two distinct phases: Phase 1 (Prepare/Promise) where a proposer seeks a quorum promise with a proposal number n, "
            "and Phase 2 (Accept/Accepted) where the proposer broadcasts an accepted value. Quorum intersection ensures that overlapping majorities guarantee safety and consistency across partition healing.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Raft decomposes consensus into three explicit subproblems: Leader Election, Log Replication, and Safety. "
            "Nodes exist in one of three states: Follower, Candidate, or Leader. Leaders maintain authority by sending periodic heartbeats (empty AppendEntries RPCs). "
            "If a follower's randomized election timer expires (typically 150ms to 300ms) without receiving a heartbeat, it transitions to candidate, increments the current term, and broadcasts RequestVote RPCs.",
            body_style,
        )
    )
    story.append(Paragraph("4. Two-Phase Commit (2PC) Protocol", h1_style))
    story.append(
        Paragraph(
            "Two-Phase Commit coordinates atomic transactions across distributed storage partitions. "
            "In the Prepare Phase, the coordinator sends a PREPARE message to all cohort participants; each participant executes the transaction locally up to the commit point, writes UNDO/REDO logs, and replies VOTE_COMMIT or VOTE_ABORT. "
            "In the Commit Phase, if all participants voted commit, the coordinator broadcasts GLOBAL_COMMIT; otherwise, it sends GLOBAL_ABORT. "
            "A major limitation of 2PC is that it is a blocking protocol: if the coordinator crashes after cohort nodes vote commit, participants remain blocked holding locks indefinitely.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph("5. Distributed Deadlock Detection and Handling", h1_style))
    story.append(
        Paragraph(
            "In distributed architectures, resources are distributed across distinct physical nodes. A distributed deadlock occurs when a global cycle of resource dependencies forms across multiple nodes, "
            "even though no single local node observes a cycle in its local Wait-For Graph (WFG). "
            "Distributed deadlock handling techniques fall into centralized, distributed, and hierarchical approaches. "
            "In centralized detection, nodes forward local WFG updates to a designated central deadlock detector. A major issue is phantom deadlocks, where network communication latency causes the detector to observe an obsolete cycle that has already resolved.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "The Chandy-Misra-Haas edge-chasing algorithm detects distributed deadlocks by propagating probe messages (initiator, sender, receiver) along the edges of the distributed WFG. "
            "If a probe message returns to its original initiator process, a global deadlock cycle exists, triggering victim selection and process rollback.",
            body_style,
        )
    )
    story.append(Paragraph("6. Byzantine Fault Tolerance and Blockchain", h1_style))
    story.append(
        Paragraph(
            "Byzantine faults refer to arbitrary or malicious node behaviors, including forging messages, sending conflicting state updates to peers, or silently dropping transactions. "
            "Lamport, Shostak, and Pease demonstrated that achieving Byzantine agreement in a synchronous system with m faulty nodes requires at least 3m + 1 total nodes and m + 1 communication rounds. "
            "Practical Byzantine Fault Tolerance (PBFT) operates efficiently in asynchronous networks using three phases: Pre-Prepare, Prepare, and Commit, tolerating up to f malicious nodes given 3f + 1 total replicas.",
            body_style,
        )
    )
    doc.build(story)
    print(f"Generated {pdf_path.name}")


def generate_database_systems_pdf():
    pdf_path = DOCS_DIR / "Database_Systems_ACID.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40
    )
    story = []

    # Page 1
    story.append(
        Paragraph(
            "Relational Database Systems: ACID Transactions & Concurrency Control", title_style
        )
    )
    story.append(
        Paragraph(
            "Course: CS304 Database Architecture | License: CC-BY 4.0 Open Educational Resource",
            meta_style,
        )
    )
    story.append(Paragraph("1. The ACID Paradigm of Database Transactions", h1_style))
    story.append(
        Paragraph(
            "A transaction is an execution unit of program code that accesses and potentially updates various database items. "
            "To preserve integrity, the DBMS guarantees the four ACID properties: "
            "Atomicity guarantees all-or-nothing execution; if any operation aborts, prior changes are undone via transaction rollback. "
            "Consistency ensures that a transaction transforms the database from one valid state satisfying all schema constraints and invariants to another valid state. "
            "Isolation ensures that concurrent transactions execute without interfering with one another, as though executed in isolation. "
            "Durability ensures that once a transaction successfully commits, its updates persist permanently on non-volatile storage even across power failures.",
            body_style,
        )
    )
    story.append(Paragraph("2. Serializability and Concurrency Anomalies", h1_style))
    story.append(
        Paragraph(
            "Concurrent execution schedules are deemed correct if they are serializable—producing the exact database state resulting from some purely serial execution of transactions. "
            "Conflict serializability evaluates whether non-conflicting adjacent operations can be swapped into a serial schedule. Two operations conflict if they belong to different transactions, access the same item, and at least one is a write. "
            "Standard ANSI SQL isolation levels protect against specific read anomalies: "
            "Dirty Read occurs when transaction T2 reads uncommitted modifications made by T1 that are subsequently rolled back. "
            "Non-Repeatable Read occurs when T1 re-reads a row and finds altered data because T2 committed an update in between. "
            "Phantom Read occurs when T1 re-executes a range query and discovers new rows inserted by committed transaction T2.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("3. Two-Phase Locking (2PL) Protocols", h1_style))
    story.append(
        Paragraph(
            "Two-Phase Locking (2PL) is a concurrency control protocol that guarantees conflict serializability. "
            "The protocol enforces two rules: 1) Growing Phase: A transaction may acquire locks (shared or exclusive) but cannot release any lock. 2) Shrinking Phase: A transaction may release locks but cannot acquire any new locks. "
            "Shared locks (S-locks) permit concurrent reads; exclusive locks (X-locks) grant sole read-write privileges.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Standard 2PL does not prevent cascading aborts. Strict Two-Phase Locking (Strict 2PL) solves this by requiring all exclusive locks to be held until the transaction finishes (commit or abort). "
            "Rigorous 2PL goes further by holding both shared and exclusive locks until the transaction terminates, ensuring strict schedules and simplifying rollback.",
            body_style,
        )
    )
    story.append(Paragraph("4. Deadlocks in Database Management Systems", h1_style))
    story.append(
        Paragraph(
            "Because transactions acquire locks incrementally, deadlocks can occur when two transactions wait for locks held by each other. "
            "DBMS engines employ two strategies: Deadlock Prevention and Deadlock Detection. "
            "Deadlock prevention protocols use transaction timestamps to avoid wait cycles before they occur: "
            "Wait-Die Scheme (Non-preemptive): If an older transaction requests a lock held by a younger transaction, the older is allowed to wait. If a younger transaction requests a lock held by an older transaction, the younger dies (is rolled back and restarted). "
            "Wound-Wait Scheme (Preemptive): If an older transaction requests a lock held by a younger transaction, the older wounds the younger, forcing it to abort and yield the lock. If a younger requests from an older, the younger is allowed to wait.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph("5. Deadlock Detection via Wait-For Graphs", h1_style))
    story.append(
        Paragraph(
            "Deadlock detection periodically constructs a directed Wait-For Graph (WFG) where vertices represent active transactions and directed edges (Ti -> Tj) indicate that Ti is waiting for Tj to release a lock. "
            "A cycle in the WFG signals a deadlock. Upon detecting a cycle, the DBMS selects a victim transaction based on rollback cost, CPU time consumed, or lock count, and aborts it to break the dependency loop.",
            body_style,
        )
    )
    story.append(Paragraph("6. Write-Ahead Logging (WAL) and ARIES Recovery", h1_style))
    story.append(
        Paragraph(
            "The Write-Ahead Logging (WAL) protocol dictates that log records describing a modification must be flushed to non-volatile disk before the corresponding dirty data page is written to database storage. "
            "Furthermore, a transaction is not considered safely committed until its COMMIT log record is forced to stable log storage. "
            "The ARIES (Algorithm for Recovery and Isolation Exploiting Semantics) algorithm executes three passes during crash recovery: "
            "1. Analysis Pass: Identifies all dirty pages in buffer pool and active uncommitted transactions at crash time. "
            "2. Redo Pass: Repeats history starting from the smallest dirty page LSN (Log Sequence Number) to restore the exact state prior to crash, redoing both committed and uncommitted operations. "
            "3. Undo Pass: Reverses the actions of all active (loser) transactions in reverse chronological order, writing Compensation Log Records (CLRs) to ensure crash-safe rollback.",
            body_style,
        )
    )
    doc.build(story)
    print(f"Generated {pdf_path.name}")


def generate_networking_protocols_pdf():
    pdf_path = DOCS_DIR / "Computer_Networking_Protocols.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter, leftMargin=35, rightMargin=35, topMargin=35, bottomMargin=35
    )
    story = []

    # Page 1 - Table heavy!
    story.append(
        Paragraph(
            "Computer Networking: Protocols, OSI Reference Model & Architectures", title_style
        )
    )
    story.append(
        Paragraph(
            "Course: CS303 Computer Networks | License: CC-BY 4.0 Open Educational Resource",
            meta_style,
        )
    )
    story.append(Paragraph("1. The 7-Layer OSI Reference Model Comparison", h1_style))
    story.append(
        Paragraph(
            "The Open Systems Interconnection (OSI) reference model organizes network communication into 7 distinct abstraction layers. The following table provides a comprehensive technical comparison across all layers:",
            body_style,
        )
    )

    osi_data = [
        [
            "Layer #",
            "Layer Name",
            "Protocol Data Unit (PDU)",
            "Primary Addressing",
            "Key Protocols",
            "Hardware / Devices",
        ],
        [
            "7",
            "Application",
            "Data / Message",
            "Names / URLs / URIs",
            "HTTP, DNS, SMTP, SSH",
            "Gateways, Firewalls",
        ],
        [
            "6",
            "Presentation",
            "Data",
            "Encoding Syntax",
            "TLS/SSL, ASCII, JPEG",
            "Software Libraries",
        ],
        [
            "5",
            "Session",
            "Data",
            "Session IDs, Tokens",
            "RPC, NetBIOS, PPTP",
            "OS Sockets, Middleware",
        ],
        [
            "4",
            "Transport",
            "Segment (TCP) / Datagram",
            "Port Numbers (16-bit)",
            "TCP, UDP, SCTP, QUIC",
            "L4 Load Balancers",
        ],
        [
            "3",
            "Network",
            "Packet",
            "IP Address (IPv4/IPv6)",
            "IPv4, IPv6, ICMP, BGP",
            "Routers, L3 Switches",
        ],
        [
            "2",
            "Data Link",
            "Frame",
            "MAC Address (48-bit)",
            "Ethernet (802.3), Wi-Fi",
            "Switches, Bridges, NICs",
        ],
        [
            "1",
            "Physical",
            "Bit Stream / Signal",
            "Frequency / Voltage",
            "1000BASE-T, RS-232",
            "Hubs, Repeaters, Cables",
        ],
    ]
    t1 = Table(osi_data, colWidths=[45, 75, 110, 105, 110, 95])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ]
        )
    )
    story.append(t1)
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # Page 2 - TCP vs UDP Table + Protocol details
    story.append(Paragraph("2. Transport Layer: TCP vs UDP Technical Specification", h1_style))
    story.append(
        Paragraph(
            "The Transport Layer delivers end-to-end communication services. Transmission Control Protocol (TCP) and User Datagram Protocol (UDP) represent contrasting transport philosophies:",
            body_style,
        )
    )

    tcp_udp_data = [
        ["Feature / Metric", "Transmission Control Protocol (TCP)", "User Datagram Protocol (UDP)"],
        [
            "Connection State",
            "Connection-Oriented (3-way handshake SYN, SYN-ACK, ACK)",
            "Connectionless (No pre-communication handshake)",
        ],
        [
            "Reliability Guarantee",
            "Guaranteed delivery with sequence numbering and ACK",
            "Best-effort delivery; packet loss possible",
        ],
        [
            "Ordering Guarantee",
            "Strict in-order packet delivery using byte sequence numbers",
            "No ordering guarantee; packets may arrive out-of-order",
        ],
        [
            "Flow & Congestion Control",
            "Sliding window flow control, Reno/Cubic congestion control",
            "None; application must handle congestion throttling",
        ],
        [
            "Header Size Overhead",
            "20 bytes minimum, up to 60 bytes with options",
            "Fixed 8 bytes (Source Port, Dest Port, Length, Checksum)",
        ],
        [
            "Transmission Mode",
            "Byte stream abstraction; segments delimited by window",
            "Discrete message datagram boundaries preserved",
        ],
        [
            "Primary Use Cases",
            "Web browsing (HTTP/HTTPS), File transfers (FTP), SSH, Email",
            "Video streaming (RTP), DNS queries, Voice over IP (VoIP)",
        ],
    ]
    t2 = Table(tcp_udp_data, colWidths=[120, 210, 210])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#99f6e4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fdfa"), colors.white]),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 10))
    story.append(Paragraph("3. Well-Known Service Port Allocations", h2_style))
    story.append(
        Paragraph(
            "Standard port numbers defined by IANA for network infrastructure services include: Port 20/21 (FTP), Port 22 (SSH), Port 25 (SMTP), Port 53 (DNS - UDP/TCP), Port 67/68 (DHCP), Port 80 (HTTP), Port 110 (POP3), Port 143 (IMAP), Port 443 (HTTPS), and Port 3306 (MySQL).",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 3 - Routing Protocols Comparison Table
    story.append(Paragraph("4. Network Layer: Dynamic Routing Protocols Comparison", h1_style))
    story.append(
        Paragraph(
            "Routing protocols compute optimal forwarding paths across complex autonomous network topologies:",
            body_style,
        )
    )

    routing_data = [
        [
            "Routing Protocol",
            "Type / Category",
            "Algorithm Basis",
            "Metric Formula",
            "Convergence Speed",
            "Administrative Distance",
        ],
        [
            "RIPv2",
            "Interior Gateway (IGP)",
            "Distance Vector (Bellman-Ford)",
            "Hop Count (Max 15 hops)",
            "Slow (count-to-infinity)",
            "120",
        ],
        [
            "OSPFv2 / v3",
            "Interior Gateway (IGP)",
            "Link State (Dijkstra SPF)",
            "Cost = 10^8 / Bandwidth",
            "Fast (hierarchical areas)",
            "110",
        ],
        [
            "IS-IS",
            "Interior Gateway (IGP)",
            "Link State (Dijkstra SPF)",
            "Interface Metric (default 10)",
            "Very Fast (sub-second)",
            "115",
        ],
        [
            "EIGRP",
            "Interior Gateway (IGP)",
            "Advanced Distance Vector (DUAL)",
            "Bandwidth + Delay composite",
            "Instantaneous with Feasible Succ.",
            "90 (Internal)",
        ],
        [
            "BGP-4",
            "Exterior Gateway (EGP)",
            "Path Vector (AS Path lists)",
            "Policy attributes (Local Pref, AS-Path, MED)",
            "Moderate (designed for stability)",
            "20 (eBGP) / 200 (iBGP)",
        ],
    ]
    t3 = Table(routing_data, colWidths=[70, 95, 125, 115, 80, 55])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338ca")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#eef2ff"), colors.white]),
            ]
        )
    )
    story.append(t3)
    story.append(Spacer(1, 10))
    story.append(Paragraph("5. Border Gateway Protocol (BGP) Mechanics", h2_style))
    story.append(
        Paragraph(
            "BGP is the path-vector routing protocol running the global core Internet. Unlike interior gateway protocols that minimize link cost, BGP routes based on autonomous system (AS) path vectors and organizational peering agreements. "
            "A BGP router establishes TCP sessions over port 179 to advertise prefix reachability through BGP UPDATE messages.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 4 - IPv4 vs IPv6 Header Table
    story.append(Paragraph("6. Internet Protocol Header Formats & Addressing", h1_style))
    story.append(
        Paragraph(
            "The network layer encapsulates transport segments into IP packets. The following table contrasts the IPv4 and IPv6 header architectures:",
            body_style,
        )
    )

    ip_hdr_data = [
        [
            "Header Attribute",
            "Internet Protocol version 4 (IPv4)",
            "Internet Protocol version 6 (IPv6)",
        ],
        [
            "Address Length",
            "32 bits (4 bytes); ~4.29 billion unique addresses",
            "128 bits (16 bytes); ~3.4 x 10^38 unique addresses",
        ],
        [
            "Base Header Size",
            "20 bytes minimum; variable with optional options field",
            "Fixed 40 bytes; extensions linked via Next Header pointer",
        ],
        [
            "Checksum Validation",
            "Header Checksum verified at every intermediate hop router",
            "No header checksum; error detection delegated to L2 and L4",
        ],
        [
            "Packet Fragmentation",
            "Allowed by intermediate routers and source endpoints",
            "Performed exclusively by the sending source endpoint",
        ],
        [
            "Configuration Model",
            "Manual static assignment or DHCP server delegation",
            "Stateless Address Autoconfiguration (SLAAC) or DHCPv6",
        ],
        [
            "Packet Lifetime",
            "Time to Live (TTL) decremented by 1 per hop router",
            "Hop Limit field decremented by 1 per hop router",
        ],
    ]
    t4 = Table(ip_hdr_data, colWidths=[120, 210, 210])
    t4.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b45309")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fffbeb"), colors.white]),
            ]
        )
    )
    story.append(t4)
    story.append(Spacer(1, 10))
    story.append(Paragraph("7. Address Resolution Protocol (ARP) & ICMP", h2_style))
    story.append(
        Paragraph(
            "ARP maps logical 32-bit IP addresses to physical 48-bit Ethernet MAC addresses within a local broadcast domain. "
            "When a host intends to transmit to an IP on the subnet without a cached MAC, it broadcasts an ARP Request (Who has 192.168.1.1? Tell 192.168.1.50). "
            "Internet Control Message Protocol (ICMP) reports network diagnostic conditions and routing errors, powering ping (Echo Request/Reply) and traceroute.",
            body_style,
        )
    )
    doc.build(story)
    print(f"Generated {pdf_path.name}")


def generate_macroeconomics_pdf():
    pdf_path = DOCS_DIR / "Principles_of_Macroeconomics.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40
    )
    story = []

    # Page 1
    story.append(
        Paragraph(
            "Principles of Macroeconomics: Monetary Policy, Fiscal Stability & Growth", title_style
        )
    )
    story.append(
        Paragraph(
            "Course: ECON201 Macroeconomic Theory | License: CC-BY 4.0 Open Educational Resource",
            meta_style,
        )
    )
    story.append(Paragraph("1. Measuring Economic Output: Gross Domestic Product (GDP)", h1_style))
    story.append(
        Paragraph(
            "Gross Domestic Product (GDP) quantifies the total monetary market value of all final goods and services produced within a country's geographical borders during a specific time period. "
            "GDP can be measured through three equivalent accounting perspectives: the expenditure approach, the income approach, and the production (value-added) approach. "
            "Under the expenditure approach, GDP equals Y = C + I + G + (X - M), where C is personal consumption expenditures, I is gross private domestic investment, G is government consumption expenditures and gross investment, and (X - M) represents net exports (exports minus imports).",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Nominal GDP evaluates output using current market prices, whereas Real GDP isolates physical production changes by using constant base-year prices. "
            "The GDP Deflator is the price index calculated as: GDP Deflator = (Nominal GDP / Real GDP) * 100. "
            "Unlike the Consumer Price Index (CPI), which tracks a fixed representative consumer basket of goods including imported items, the GDP deflator reflects all domestically produced goods and automatically adjusts weights as expenditure patterns shift.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("2. Inflation, Unemployment, and the Phillips Curve", h1_style))
    story.append(
        Paragraph(
            "Inflation measures the sustained percentage increase in the general price level over time. "
            "Unemployment is divided into three fundamental categories: "
            "1. Frictional Unemployment: Occurs when workers are voluntarily transitioning between jobs or entering the labor market. "
            "2. Structural Unemployment: Arises when a permanent structural mismatch exists between workers' skills and employer requirements, often driven by technological automation or globalization. "
            "3. Cyclical Unemployment: Direct result of a macroeconomic downturn or recession where aggregate demand falls below potential output.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "The short-run Phillips Curve demonstrates an inverse empirical relationship between inflation and unemployment: when aggregate demand expands, unemployment drops, driving wage pressures and inflation higher. "
            "However, Milton Friedman and Edmund Phelps formulated the Natural Rate Hypothesis, establishing that in the long run, the Phillips Curve is vertical at the Natural Rate of Unemployment (NAIRU). "
            "In the long run, expectations adjust, and expansionary monetary stimulus results purely in higher inflation without durable employment gains.",
            body_style,
        )
    )
    story.append(Paragraph("3. The IS-LM Framework of Equilibrium", h1_style))
    story.append(
        Paragraph(
            "The IS-LM model synthesizes the goods market and money market to determine national output and interest rates simultaneously. "
            "The IS curve (Investment-Saving) represents equilibrium in the goods market; it slopes downward because higher interest rates reduce investment spending, lowering total equilibrium output. "
            "The LM curve (Liquidity Preference-Money Supply) represents equilibrium in the money market; it slopes upward because higher national income increases real money transaction demand, pushing interest rates upward for a given real money supply.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph("4. Central Banking and Monetary Policy Instruments", h1_style))
    story.append(
        Paragraph(
            "Central banks govern domestic macroeconomic stability through monetary policy. The primary conventional tools include: "
            "1. Open Market Operations (OMO): The buying and selling of government treasury securities to influence commercial banking reserves and the short-term policy interest rate (such as the Federal Funds Rate). "
            "2. Reserve Requirements: The mandatory minimum percentage of deposits that commercial depository institutions must hold in reserve rather than lend out. "
            "3. Discount Rate: The interest rate charged to commercial banks when borrowing directly from the central bank discount window.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "When conventional interest rates hit the Zero Lower Bound (ZLB), central banks engage in unconventional monetary policy known as Quantitative Easing (QE). "
            "Under QE, the central bank creates central bank reserves to execute large-scale asset purchases of long-term government bonds and mortgage-backed securities, directly depressing long-term yields and stimulating capital borrowing.",
            body_style,
        )
    )
    story.append(Paragraph("5. Fiscal Policy and the Keynesian Multiplier", h1_style))
    story.append(
        Paragraph(
            "Fiscal policy represents government decisions regarding public expenditure and taxation levels. "
            "The simple Keynesian Government Spending Multiplier is formulated as: Multiplier = 1 / (1 - MPC), where MPC is the Marginal Propensity to Consume. "
            "For instance, if MPC is 0.8, an initial increase in government infrastructure expenditure of $10 billion yields a total expansion in aggregate output of $50 billion. "
            "However, government borrowing can drive up market interest rates, resulting in the Crowding-Out Effect, where private investment expenditure is partially displaced.",
            body_style,
        )
    )
    doc.build(story)
    print(f"Generated {pdf_path.name}")


def generate_cell_biology_pdf():
    pdf_path = DOCS_DIR / "Cell_Biology_and_Metabolism.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40
    )
    story = []

    # Page 1
    story.append(
        Paragraph(
            "Cell Biology & Metabolic Biochemistry: Cellular Energetics & Respiration", title_style
        )
    )
    story.append(
        Paragraph(
            "Course: BIO101 Molecular & Cellular Biology | License: CC-BY 4.0 Open Educational Resource",
            meta_style,
        )
    )
    story.append(Paragraph("1. Structural Organization of the Eukaryotic Cell", h1_style))
    story.append(
        Paragraph(
            "The cell represents the fundamental structural and functional unit of all living organisms. "
            "Eukaryotic cells are distinguished by membrane-bound organelles that partition biochemical processes into distinct micro-environments. "
            "The nucleus houses genomic DNA packaged into chromatin by histone proteins. "
            "The Endoplasmic Reticulum (ER) includes the Rough ER, studded with ribosomes synthesizing membrane and secretory proteins, and the Smooth ER, which synthesizes lipids, phospholipids, and steroid hormones while detoxifying metabolic byproducts. "
            "The Golgi apparatus modifies, sorts, and packages glycoproteins into transport vesicles targeted for cellular secretion or lysosomes.",
            body_style,
        )
    )
    story.append(Paragraph("2. Thermodynamics and Enzyme Kinetics", h1_style))
    story.append(
        Paragraph(
            "Biological chemical reactions obey the laws of thermodynamics. Gibbs free energy change (delta G) dictates reaction spontaneity: exergonic reactions release free energy (delta G < 0), whereas endergonic reactions require energy input (delta G > 0). "
            "Enzymes are biological catalysts that increase reaction velocity by lowering the activation energy barrier without altering the reaction equilibrium or net delta G. "
            "The Michaelis-Menten kinetic model describes enzyme reaction rates: V0 = (Vmax * [S]) / (Km + [S]), where Vmax is the maximum reaction velocity, [S] is substrate concentration, and Km (Michaelis constant) represents the substrate concentration at which reaction rate is half of Vmax. A lower Km reflects higher enzyme-substrate affinity.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("3. Cellular Respiration Stage 1: Glycolysis", h1_style))
    story.append(
        Paragraph(
            "Cellular respiration is the catabolic pathway that oxidizes organic fuels to generate adenosine triphosphate (ATP). "
            "Glycolysis occurs in the cytoplasm and does not require molecular oxygen. It converts one molecule of 6-carbon glucose into two molecules of 3-carbon pyruvate through 10 enzymatic reactions. "
            "The pathway consists of two phases: 1) Energy Investment Phase: Two ATP molecules are consumed by hexokinase and phosphofructokinase-1 (PFK-1, the key rate-limiting committed step). "
            "2) Energy Payoff Phase: Four ATP molecules are generated via substrate-level phosphorylation, alongside two molecules of NADH. Thus, the net yield of glycolysis is 2 ATP, 2 NADH, and 2 pyruvate molecules per glucose.",
            body_style,
        )
    )
    story.append(Paragraph("4. The Citric Acid Cycle (Krebs Cycle)", h1_style))
    story.append(
        Paragraph(
            "In the presence of oxygen, pyruvate translocates into the mitochondrial matrix. The pyruvate dehydrogenase complex executes oxidative decarboxylation, converting pyruvate into 2-carbon Acetyl-CoA, producing 1 CO2 and 1 NADH per pyruvate. "
            "Acetyl-CoA enters the Citric Acid Cycle by condensing with 4-carbon oxaloacetate to form 6-carbon citrate, catalyzed by citrate synthase. "
            "Across one complete turn of the cycle, two carbons are released as CO2, yielding 3 NADH, 1 FADH2, and 1 ATP (or GTP) via substrate-level phosphorylation. "
            "Because one glucose yields two Acetyl-CoA molecules, the total Krebs cycle yield per glucose is 6 NADH, 2 FADH2, 2 ATP, and 4 CO2.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph("5. Oxidative Phosphorylation and ATP Synthase", h1_style))
    story.append(
        Paragraph(
            "Oxidative phosphorylation occurs at the inner mitochondrial membrane and produces the vast majority of cellular ATP. "
            "The Electron Transport Chain (ETC) comprises four multiprotein complexes (Complex I, II, III, and IV). High-energy electrons donated by NADH (at Complex I) and FADH2 (at Complex II) pass through coenzyme Q (ubiquinone) and cytochrome c to Complex IV, where molecular oxygen serves as the terminal electron acceptor, reducing to form water (H2O).",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "As electrons flow exergonically through Complexes I, III, and IV, protons (H+) are actively pumped from the mitochondrial matrix into the intermembrane space, generating a steep electrochemical proton gradient (proton-motive force). "
            "Peter Mitchell's chemiosmotic hypothesis explains how ATP synthase harnesses this potential energy. "
            "Protons flow down their electrochemical gradient through the F0 channel of ATP synthase, driving rotational conformational changes in the F1 catalytic subunit that phosphorylate ADP and inorganic phosphate (Pi) into ATP. "
            "Theoretical maximum ATP yield from complete aerobic respiration is 30 to 32 ATP molecules per oxidized glucose molecule.",
            body_style,
        )
    )
    story.append(Paragraph("6. Fermentation: Anaerobic ATP Generation", h1_style))
    story.append(
        Paragraph(
            "When molecular oxygen is absent, oxidative phosphorylation ceases and NADH cannot transfer electrons to the ETC. "
            "To sustain glycolysis, cells must regenerate NAD+ from NADH through fermentation. "
            "In lactic acid fermentation (e.g. human skeletal muscle during intense exercise), lactate dehydrogenase reduces pyruvate to lactate while oxidizing NADH to NAD+. "
            "In alcoholic fermentation (e.g. yeast), pyruvate is first decarboxylated to acetaldehyde by pyruvate decarboxylase, then reduced to ethanol by alcohol dehydrogenase, regenerating NAD+.",
            body_style,
        )
    )
    doc.build(story)
    print(f"Generated {pdf_path.name}")


if __name__ == "__main__":
    generate_distributed_systems_pdf()
    generate_database_systems_pdf()
    generate_networking_protocols_pdf()
    generate_macroeconomics_pdf()
    generate_cell_biology_pdf()
    print("All 5 diverse sample documents generated successfully.")
