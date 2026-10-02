from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


def create_sample_study_pdfs():
    out_dir = Path(__file__).resolve().parent / "sample_docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )

    # 1. Operating Systems Notes
    os_pdf_path = out_dir / "Operating_Systems_Concurrency.pdf"
    doc_os = SimpleDocTemplate(
        str(os_pdf_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    story_os = []

    story_os.append(Paragraph("Operating Systems: Process Management & Concurrency", title_style))
    story_os.append(
        Paragraph(
            "<b>Course:</b> CS301 Operating Systems Architecture | <b>Author:</b> Dept. of Computer Science",
            body_style,
        )
    )
    story_os.append(Spacer(1, 10))

    story_os.append(Paragraph("1. Process Concept and Process Control Block (PCB)", h2_style))
    story_os.append(
        Paragraph(
            "A process is defined as a program in execution. It encompasses the executable code (text section), "
            "current activity tracked by the Program Counter (PC) and processor registers, a process stack containing temporary data "
            "(function parameters, return addresses, local variables), a data section containing global variables, and a heap for runtime dynamic memory allocation.",
            body_style,
        )
    )
    story_os.append(
        Paragraph(
            "The Process Control Block (PCB) is the central operating system data structure used to maintain all information associated with an active process. "
            "Key fields inside a PCB include: Process State (New, Ready, Running, Waiting, Terminated), Program Counter indicating the next instruction, "
            "CPU registers (accumulators, index registers, stack pointers), CPU-scheduling information such as priority and queue pointers, "
            "Memory-management information (page tables, base and limit registers), and Accounting/I/O status information including open file descriptors.",
            body_style,
        )
    )

    story_os.append(Paragraph("2. Threads vs Processes", h2_style))
    story_os.append(
        Paragraph(
            "A thread is the smallest schedulable unit of CPU utilization, commonly termed a lightweight process. "
            "Threads belonging to the same process share their code section, data section, and OS resources (such as open files and signals). "
            "However, each thread maintains its own unique Thread ID, Program Counter, register set, and private execution stack.",
            body_style,
        )
    )
    story_os.append(
        Paragraph(
            "Key benefits of multithreading include: High responsiveness in interactive applications, efficient resource sharing without costly IPC, "
            "economy due to lower context switching overhead, and scalability across multicore and multiprocessor hardware architectures.",
            body_style,
        )
    )

    story_os.append(PageBreak())

    story_os.append(Paragraph("3. Critical-Section Problem & Synchronization", h2_style))
    story_os.append(
        Paragraph(
            "A race condition occurs when multiple concurrent threads or processes access and manipulate shared data, and the final outcome depends on the arbitrary execution order. "
            "To guarantee deterministic execution, critical sections must be synchronized.",
            body_style,
        )
    )
    story_os.append(
        Paragraph(
            "Any valid solution to the Critical-Section Problem must satisfy three mandatory requirements:<br/>"
            "1. <b>Mutual Exclusion:</b> If process Pi is executing in its critical section, no other process can be executing in its critical section.<br/>"
            "2. <b>Progress:</b> If no process is executing in its critical section and some processes wish to enter, only those processes not in their remainder section can participate in deciding who enters next, and selection cannot be postponed indefinitely.<br/>"
            "3. <b>Bounded Waiting:</b> There must exist a bound on the number of times other processes are allowed to enter their critical sections after a process has requested entry and before that request is granted.",
            body_style,
        )
    )

    story_os.append(Paragraph("4. Semaphores and Mutex Locks", h2_style))
    story_os.append(
        Paragraph(
            "A Mutex Lock is a boolean synchronization lock: a process must acquire the lock before entering its critical section and release it upon departure. "
            "A Semaphore is an integer synchronization variable introduced by Edsger Dijkstra, manipulated strictly through two atomic operations: wait() and signal().",
            body_style,
        )
    )
    story_os.append(
        Paragraph(
            "<b>Counting Semaphores</b> range over an unrestricted domain to control access to finite resource pools. "
            "<b>Binary Semaphores</b> have an integer value constrained to 0 and 1, functioning identically to mutexes.",
            body_style,
        )
    )

    story_os.append(PageBreak())

    story_os.append(Paragraph("5. Deadlocks: The Four Necessary Conditions", h2_style))
    story_os.append(
        Paragraph(
            "A deadlock is a condition in which a set of concurrent processes are permanently blocked because each process holds a resource and waits for another resource held by another process in the set.",
            body_style,
        )
    )
    story_os.append(
        Paragraph(
            "Coffman et al. established that a deadlock can arise if and only if the four following conditions hold simultaneously:<br/>"
            "1. <b>Mutual Exclusion:</b> At least one resource must be held in a non-shareable mode.<br/>"
            "2. <b>Hold and Wait:</b> A process must currently hold at least one resource and request additional resources held by other processes.<br/>"
            "3. <b>No Preemption:</b> Resources cannot be forcibly seized; they can only be voluntarily released by the holding process.<br/>"
            "4. <b>Circular Wait:</b> A closed chain of processes exists where each process holds resources required by the subsequent process in the loop.",
            body_style,
        )
    )
    story_os.append(
        Paragraph(
            "<b>Handling Strategies:</b> Deadlock Prevention (invalidating at least one of the 4 conditions), Deadlock Avoidance (e.g. Dijkstra's Banker's Algorithm ensuring system always remains in a safe state), and Deadlock Detection with recovery.",
            body_style,
        )
    )

    doc_os.build(story_os)
    print(f"Created: {os_pdf_path}")


if __name__ == "__main__":
    create_sample_study_pdfs()
