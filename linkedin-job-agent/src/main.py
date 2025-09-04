"""CLI interface for LinkedIn Job Agent."""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import Settings, get_settings
from .database.models import create_session, get_database_url
from .database.repository import ApplicationRepository
from .linkedin.browser import LinkedInBrowser
from .resume.ai_parser import AIResumeParser
from .utils.logger import setup_logging

console = Console()


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx, debug):
    """LinkedIn Job Application Agent - Automated job search and application."""
    ctx.ensure_object(dict)
    settings = get_settings()
    if debug:
        settings.debug = True
    ctx.obj["settings"] = settings
    setup_logging(settings.debug)


@cli.command()
@click.option("--resume", "-r", required=True, type=click.Path(exists=True), help="Resume file path (PDF/DOCX)")
@click.option("--keywords", "-k", help="Job search keywords")
@click.option("--location", "-l", help="Job location")
@click.option("--remote", is_flag=True, help="Search for remote jobs")
@click.option("--limit", "-n", default=50, help="Maximum number of jobs to process")
@click.option("--dry-run", is_flag=True, help="Run without applying")
@click.option("--auto-apply", is_flag=True, help="Automatically apply to matched jobs")
@click.pass_context
def search(ctx, resume, keywords, location, remote, limit, dry_run, auto_apply):
    """Search for jobs and apply based on resume."""
    settings = ctx.obj["settings"]

    if dry_run:
        settings.dry_run = True
        console.print("[yellow]Running in dry-run mode - no applications will be submitted[/yellow]")

    if auto_apply:
        settings.auto_apply = True
        console.print("[yellow]Auto-apply enabled - will apply to all matched jobs[/yellow]")

    # Run the async search
    asyncio.run(search_and_apply(
        settings=settings,
        resume_path=resume,
        keywords=keywords,
        location=location or settings.default_location,
        remote=remote,
        limit=limit,
    ))


async def search_and_apply(
    settings: Settings,
    resume_path: str,
    keywords: str | None,
    location: str,
    remote: bool,
    limit: int
):
    """Main search and apply workflow."""
    console.print("\n[bold cyan]LinkedIn Job Application Agent[/bold cyan]\n")

    # Step 1: Parse resume using AI
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Parsing resume with AI...", total=None)

        parser = AIResumeParser()
        try:
            resume_data = await parser.parse(resume_path)
            
            # Also get the raw text for later use
            resume_text = resume_data["raw_text"]
            
            console.print(f"✓ Resume parsed: [green]{resume_data.get('name', 'Unknown')}[/green]")
            
            # Display skills if available
            if 'skills' in resume_data and resume_data['skills']:
                skills_display = resume_data['skills'][:10] if isinstance(resume_data['skills'], list) else str(resume_data['skills'])[:100]
                if isinstance(skills_display, list):
                    console.print(f"  Skills: {', '.join(skills_display)}")
                else:
                    console.print(f"  Skills: {skills_display}")
        except Exception as e:
            console.print(f"[red]Failed to parse resume: {e}[/red]")
            return

        progress.remove_task(task)

    # Step 2: Get search keywords from AI
    console.print(f"  AI suggested keywords: [cyan]{resume_data["keywords"]}[/cyan]")

    # Step 3: Initialize browser
    console.print("\n[bold]Initializing browser...[/bold]")
    browser = LinkedInBrowser(settings)

    try:
        await browser.initialize()

        # Check if logged in
        is_logged_in = await browser.check_logged_in()

        if not is_logged_in:
            console.print("Not logged in to LinkedIn. Attempting login...")

            if not settings.linkedin_email or not settings.linkedin_password:
                console.print("[red]LinkedIn credentials not configured in .env file[/red]")
                await browser.close()
                return

            success = await browser.login(settings.linkedin_email, settings.linkedin_password)
            if not success:
                console.print("[red]Failed to login to LinkedIn[/red]")
                await browser.close()
                return

        console.print("[green]✓ Connected to LinkedIn[/green]")

        # Step 4: Search for jobs
        if keywords:
            console.print(f"\n[bold]Searching for: {keywords} in {location}[/bold]")
        else:
            console.print("\n[bold]Getting LinkedIn recommended jobs[/bold]")
        await browser.search_jobs(resume_data["keywords"], resume_data["location"], remote)

        # Step 5: Use human-like application flow
        from .linkedin.human_flow import HumanJobApplicant
        
        applicant = HumanJobApplicant(
            page=browser.page,
            resume_text=resume_text,
            ai_parser=parser
        )
        
        # Apply to jobs like a human would
        total_applied = await applicant.apply_to_jobs(
            max_jobs=limit,
            min_match_score=settings.min_match_score
        )
        
        console.print(f"\n[bold green]Session complete![/bold green]")
        console.print(f"  Applications submitted: {total_applied}")
        
        if settings.dry_run:
            console.print("[yellow]Dry run mode - no actual applications were submitted[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        await browser.close()




@cli.command()
@click.pass_context
def stats(ctx):
    """Show application statistics."""
    ctx.obj["settings"]

    db_session = create_session(get_database_url())
    repo = ApplicationRepository(db_session)

    stats = repo.get_stats()

    console.print("\n[bold cyan]Application Statistics[/bold cyan]\n")
    console.print(f"Total Applications: [green]{stats['total_applications']}[/green]")

    if stats['status_breakdown']:
        console.print("\nStatus Breakdown:")
        for status, count in stats['status_breakdown'].items():
            console.print(f"  {status}: {count}")

    console.print(f"\nAverage Match Score: [cyan]{stats['average_match_score']:.0%}[/cyan]")

    if stats['top_companies']:
        console.print("\nTop Companies:")
        for company_info in stats['top_companies'][:5]:
            console.print(f"  {company_info['company']}: {company_info['count']} applications")


@cli.command()
@click.pass_context
def setup(ctx):
    """Set up the application environment."""
    console.print("[bold cyan]LinkedIn Job Agent Setup[/bold cyan]\n")

    # Create .env file
    if not Path(".env").exists():
        from .config import create_env_example
        create_env_example()
        console.print("✓ Created .env.example file")
        console.print("[yellow]Please copy .env.example to .env and configure your credentials[/yellow]")

    # Check Docker
    console.print("\nTo start the database, run:")
    console.print("[cyan]docker-compose -f docker/docker-compose.yml up -d[/cyan]")

    # Install Playwright browsers
    console.print("\nTo install Playwright browsers, run:")
    console.print("[cyan]playwright install chromium[/cyan]")

    console.print("\n[green]Setup complete![/green]")


if __name__ == "__main__":
    cli()
