#!/usr/bin/env python3
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from markdown_to_html import convert_markdown


class PublishWorkflow:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def publish_file(self, input_path, output_path, css_path=None, include_toc=False):
        start = time.time()
        try:
            result = convert_markdown(input_path, output_path, css_path,
                                     include_toc=include_toc, show_stats=True)
            elapsed = time.time() - start
            stats = result.get('stats', {}) if isinstance(result, dict) else {}
            return {
                'input': str(input_path),
                'output': str(output_path),
                'success': True,
                'elapsed_seconds': round(elapsed, 3),
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                'input': str(input_path),
                'output': str(output_path),
                'success': False,
                'elapsed_seconds': round(elapsed, 3),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def publish_directory(self, input_dir, output_dir, css_path=None, include_toc=False, pattern='*.md'):
        output_dir.mkdir(parents=True, exist_ok=True)
        md_files = list(input_dir.glob(pattern))
        results = []
        for md_file in md_files:
            output_file = output_dir / f'{md_file.stem}.html'
            result = self.publish_file(md_file, output_file, css_path, include_toc)
            results.append(result)
            status = '✓' if result['success'] else '✗'
            print(f'  {status} {md_file.name} -> {output_file.name}')
        return results
    
    def save_results(self, output_path, summary=None):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        full_results = {
            'workflow': 'publish',
            'started_at': self.start_time.isoformat() if self.start_time else None,
            'completed_at': self.end_time.isoformat() if self.end_time else None,
            'total_files': len(self.results),
            'successful': sum(1 for r in self.results if r['success']),
            'failed': sum(1 for r in self.results if not r['success']),
            'files': self.results,
        }
        if summary:
            full_results['summary'] = summary
        with open(output_path, 'w') as f:
            json.dump(full_results, f, indent=2)
        return full_results


def main():
    parser = argparse.ArgumentParser(description='Publish Markdown files to HTML')
    parser.add_argument('--input', '-i', type=Path, required=True)
    parser.add_argument('--output', '-o', type=Path, required=True)
    parser.add_argument('--css', type=Path)
    parser.add_argument('--include-toc', '-t', action='store_true')
    parser.add_argument('--log', '-l', type=Path)
    parser.add_argument('--pattern', '-p', default='*.md')
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f'Error: Input path {args.input} does not exist', file=sys.stderr)
        sys.exit(1)
    if args.css and not args.css.exists():
        print(f'Error: CSS file {args.css} not found', file=sys.stderr)
        sys.exit(1)
    
    workflow = PublishWorkflow()
    workflow.start_time = datetime.now()
    
    print(f'Publish workflow started at {workflow.start_time.isoformat()}')
    print(f'   Input: {args.input}')
    print(f'   Output: {args.output}')
    
    if args.input.is_file():
        if args.output.is_dir():
            output_file = args.output / f'{args.input.stem}.html'
        else:
            output_file = args.output
        result = workflow.publish_file(args.input, output_file, args.css, args.include_toc)
        workflow.results.append(result)
    else:
        workflow.results = workflow.publish_directory(args.input, args.output, args.css, args.include_toc, args.pattern)
    
    workflow.end_time = datetime.now()
    duration = (workflow.end_time - workflow.start_time).total_seconds()
    
    successful = sum(1 for r in workflow.results if r['success'])
    failed = sum(1 for r in workflow.results if not r['success'])
    print(f'Results: {successful} succeeded, {failed} failed ({duration:.2f}s)')
    
    if args.log:
        workflow.save_results(args.log)
        print(f'Results logged to {args.log}')
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
