"""Command-line interface for Spira integration tool."""

import sys
import logging
from pathlib import Path

from .config.config_manager import ConfigurationManager, create_argument_parser
from .parsers.parser_factory import ParserFactory
from .logging_config import setup_logging


def main():
    """Main entry point for CLI."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Load configuration
        logger.info("Loading configuration...")
        config_manager = ConfigurationManager()
        config = config_manager.load_from_args(args)
        config_manager.validate()
        
        # Log masked configuration
        masked_config = config_manager.get_masked_config()
        logger.info(f"Configuration loaded: {masked_config}")
        
        # Create parser factory
        parser_factory = ParserFactory()
        
        # Detect or use specified result type
        if config.result_type:
            result_type = config.result_type
            logger.info(f"Using specified result type: {result_type}")
        else:
            result_type = parser_factory.detect_result_type(config.results_file)
            logger.info(f"Detected result type: {result_type}")
        
        # Get parser and parse results
        logger.info(f"Parsing test results from: {config.results_file}")
        test_parser = parser_factory.get_parser(result_type)
        test_results = test_parser.parse(config.results_file)
        
        logger.info(f"Successfully parsed {len(test_results)} test results")
        
        # Display results summary
        passed = sum(1 for r in test_results if r.status.name == 'PASSED')
        failed = sum(1 for r in test_results if r.status.name == 'FAILED')
        skipped = sum(1 for r in test_results if r.status.name == 'SKIPPED')
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total tests: {len(test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print("="*60)
        
        # Display individual results
        print("\nTest Details:")
        for i, result in enumerate(test_results, 1):
            status_symbol = "✓" if result.status.name == "PASSED" else "✗" if result.status.name == "FAILED" else "○"
            print(f"{i}. {status_symbol} {result.name} [{result.status.name}]")
            if result.error_message:
                print(f"   Error: {result.error_message}")
        
        print("\n" + "="*60)
        print("NOTE: Spira API integration not yet implemented")
        print("This demo shows parsing functionality only")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
