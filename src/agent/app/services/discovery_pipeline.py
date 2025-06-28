import time
from datetime import datetime
from typing import List, Dict, Any
import logging
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor

from app.db.database import SessionLocal
from app.services.chat_service import discover_tools

logger = logging.getLogger(__name__)

class DiscoveryPipeline:
    """Enterprise-grade automated discovery pipeline"""
    
    def __init__(self):
        self.is_running = False
        self.delay_between_categories = 4
        
    def run_intensive_discovery(self, target_tools: int = 500) -> Dict[str, Any]:
        """Intensive discovery mode for rapid scaling"""
        
        # All AI categories for comprehensive discovery
        categories = [
            "ai_writing_tools", "ai_image_generation", "ai_video_tools", "ai_audio_tools",
            "ai_coding_tools", "ai_data_analysis", "ai_marketing_tools", "ai_customer_service",
            "ai_hr_tools", "ai_finance_tools", "ai_education_tools", "ai_research_tools",
            "ai_3d_modeling", "ai_gaming_tools", "desktop_applications", "browser_extensions",
            "mobile_apps", "web_applications", "ai_services", "code_editors", 
            "plugins", "creative_tools", "business_tools", "productivity_tools"
        ]
        
        results = {
            "pipeline_id": f"intensive_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_discovered": 0,
            "total_saved": 0,
            "total_updated": 0,
            "categories_processed": 0,
            "category_results": [],
            "errors": []
        }
        
        print(f"🚀 INTENSIVE DISCOVERY MODE STARTED")
        print(f"🎯 Target: {target_tools} tools across {len(categories)} categories")
        
        db = SessionLocal()
        
        try:
            for i, category in enumerate(categories):
                if results["total_saved"] >= target_tools:
                    print(f"🎉 TARGET REACHED! {results['total_saved']} tools discovered")
                    break
                
                category_start = time.time()
                print(f"\n📋 Processing {i+1}/{len(categories)}: {category}")
                
                try:
                    result = discover_tools(category, db)
                    category_time = time.time() - category_start
                    
                    if result.get("success"):
                        saved = result.get("database_result", {}).get("saved", 0)
                        updated = result.get("database_result", {}).get("updated", 0)
                        
                        results["total_saved"] += saved
                        results["total_updated"] += updated
                        results["categories_processed"] += 1
                        
                        print(f"  ✅ SUCCESS: {saved} new, {updated} updated ({category_time:.1f}s)")
                        
                        results["category_results"].append({
                            "category": category,
                            "success": True,
                            "saved": saved,
                            "updated": updated,
                            "processing_time": round(category_time, 2)
                        })
                    else:
                        error = result.get("error", "Unknown error")
                        print(f"  ❌ FAILED: {error}")
                        results["errors"].append(f"{category}: {error}")
                
                except Exception as e:
                    error_msg = f"Exception in {category}: {str(e)}"
                    print(f"  💥 ERROR: {error_msg}")
                    results["errors"].append(error_msg)
                
                # Progress update
                progress = (i + 1) / len(categories) * 100
                print(f"  📊 Progress: {progress:.1f}% | Total tools: {results['total_saved']}")
                
                # Delay between categories
                if i < len(categories) - 1:
                    print(f"  ⏳ Cooling down {self.delay_between_categories}s...")
                    time.sleep(self.delay_between_categories)
                    
        finally:
            db.close()
            
        results["end_time"] = datetime.utcnow().isoformat()
        
        print(f"\n🎊 INTENSIVE DISCOVERY COMPLETE!")
        print(f"📈 RESULTS:")
        print(f"   • New tools discovered: {results['total_saved']}")
        print(f"   • Existing tools updated: {results['total_updated']}")
        print(f"   • Categories processed: {results['categories_processed']}")
        
        return results

    def run_mega_scaling_pipeline(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Mega scaling pipeline to reach large numbers of tools"""
        
        strategies = [
            {"name": "Popular Tools", "prompt_suffix": "Find the most popular and well-known tools"},
            {"name": "Emerging Tools", "prompt_suffix": "Focus on newer, emerging tools and startups"}, 
            {"name": "Open Source", "prompt_suffix": "Look for open-source and free alternatives"},
            {"name": "Enterprise", "prompt_suffix": "Find enterprise and premium tools"},
            {"name": "Niche Tools", "prompt_suffix": "Discover niche and specialized tools"}
        ]
        
        categories = [
            "ai_writing_tools", "ai_image_generation", "ai_video_tools", "ai_audio_tools",
            "ai_coding_tools", "ai_data_analysis", "ai_marketing_tools", "ai_customer_service",
            "ai_hr_tools", "ai_finance_tools", "ai_education_tools", "ai_research_tools",
            "ai_3d_modeling", "ai_gaming_tools", "desktop_applications", "browser_extensions",
            "mobile_apps", "web_applications", "ai_services", "code_editors", 
            "plugins", "creative_tools", "business_tools", "productivity_tools"
        ]
        
        results = {
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0,
            "rounds_completed": 0,
            "strategy_breakdown": {}
        }
        
        print(f"🌟 MEGA SCALING STARTED - Target: {target_tools} tools")
        
        db = SessionLocal()
        round_num = 0
        
        try:
            while results["total_saved"] < target_tools and round_num < 8:  # Max 8 rounds
                round_num += 1
                strategy = strategies[(round_num - 1) % len(strategies)]
                
                print(f"\n🚀 ROUND {round_num}: {strategy['name']}")
                round_saved = 0
                
                for category in categories:
                    if results["total_saved"] >= target_tools:
                        break
                        
                    try:
                        result = self._discover_with_strategy(category, strategy, db)
                        
                        if result.get("success"):
                            saved = result.get("database_result", {}).get("saved", 0)
                            results["total_saved"] += saved
                            round_saved += saved
                            
                            if saved > 0:
                                print(f"  ✅ {category}: +{saved}")
                    
                    except Exception as e:
                        pass
                    
                    time.sleep(1)  # Fast processing
                
                results["rounds_completed"] += 1
                print(f"🎯 Round {round_num}: +{round_saved} tools | Total: {results['total_saved']}")
                
                if round_num < 8 and results["total_saved"] < target_tools:
                    time.sleep(5)  # Short break
                    
        finally:
            db.close()
        
        print(f"🎊 MEGA SCALING COMPLETE: {results['total_saved']} tools added!")
        return results

    def run_turbo_discovery(self, target_tools: int = 2000) -> Dict[str, Any]:
        """Ultra-fast parallel discovery pipeline - 3x faster than sequential"""
        
        categories = [
            "ai_writing_tools", "ai_image_generation", "ai_video_tools", "ai_audio_tools",
            "ai_coding_tools", "ai_data_analysis", "ai_marketing_tools", "ai_customer_service",
            "ai_hr_tools", "ai_finance_tools", "ai_education_tools", "ai_research_tools",
            "ai_3d_modeling", "ai_gaming_tools", "desktop_applications", "browser_extensions",
            "mobile_apps", "web_applications", "ai_services", "code_editors", 
            "plugins", "creative_tools", "business_tools", "productivity_tools"
        ]
        
        results = {
            "turbo_id": f"turbo_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "target_tools": target_tools,
            "total_saved": 0,
            "total_updated": 0,
            "batches_completed": 0,
            "batch_results": [],
            "processing_mode": "parallel"
        }
        
        print(f"🚀 TURBO DISCOVERY MODE - Parallel Processing")
        print(f"🎯 Target: {target_tools} tools")
        print(f"⚡ Processing 4 categories simultaneously")
        print(f"🔄 Expected batches: {len(categories) // 4}")
        
        db = SessionLocal()
        max_workers = 4  # Process 4 categories in parallel
        
        try:
            # Process categories in parallel batches of 4
            for i in range(0, len(categories), max_workers):
                if results["total_saved"] >= target_tools:
                    print(f"🎉 TARGET REACHED! {results['total_saved']} tools discovered")
                    break
                    
                batch = categories[i:i + max_workers]
                batch_num = i // max_workers + 1
                
                print(f"\n⚡ Batch {batch_num}: Processing {len(batch)} categories in parallel")
                batch_start = time.time()
                
                # Use ThreadPoolExecutor for parallel processing
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all categories in batch to thread pool
                    future_to_category = {
                        executor.submit(self._discover_category_turbo, category, db): category 
                        for category in batch
                    }
                    
                    # Collect results as they complete
                    batch_saved = 0
                    batch_updated = 0
                    batch_errors = []
                    
                    for future in future_to_category:
                        category = future_to_category[future]
                        try:
                            result = future.result(timeout=90)  # 90 second timeout per category
                            
                            if result.get("success"):
                                saved = result.get("database_result", {}).get("saved", 0)
                                updated = result.get("database_result", {}).get("updated", 0)
                                
                                batch_saved += saved
                                batch_updated += updated
                                results["total_saved"] += saved
                                results["total_updated"] += updated
                                
                                print(f"  ✅ {category}: +{saved} new, +{updated} updated")
                            else:
                                error = result.get("error", "Unknown error")
                                batch_errors.append(f"{category}: {error}")
                                print(f"  ❌ {category}: {error}")
                                
                        except Exception as e:
                            batch_errors.append(f"{category}: {str(e)}")
                            print(f"  💥 {category}: {str(e)}")
                
                batch_time = time.time() - batch_start
                results["batches_completed"] += 1
                
                # Record batch results
                batch_result = {
                    "batch_number": batch_num,
                    "categories": batch,
                    "tools_saved": batch_saved,
                    "tools_updated": batch_updated,
                    "processing_time": round(batch_time, 2),
                    "errors": batch_errors,
                    "cumulative_total": results["total_saved"]
                }
                results["batch_results"].append(batch_result)
                
                print(f"🎯 Batch {batch_num} Complete:")
                print(f"    • New tools: {batch_saved}")
                print(f"    • Updated tools: {batch_updated}") 
                print(f"    • Batch time: {batch_time:.1f}s")
                print(f"    • Total tools: {results['total_saved']}")
                print(f"    • Progress: {(results['total_saved']/target_tools)*100:.1f}%")
                
                # Short delay between batches (much faster than sequential)
                if results["total_saved"] < target_tools and i + max_workers < len(categories):
                    print(f"    ⏳ Cooling down 2s before next batch...")
                    time.sleep(2)  # Reduced from 4s to 2s
                    
        finally:
            db.close()
            
        results["end_time"] = datetime.utcnow().isoformat()
        total_time = sum(batch.get("processing_time", 0) for batch in results["batch_results"])
        results["total_processing_time"] = total_time
        
        print(f"\n🎊 TURBO DISCOVERY COMPLETE!")
        print(f"📈 RESULTS:")
        print(f"   • New tools discovered: {results['total_saved']}")
        print(f"   • Existing tools updated: {results['total_updated']}")
        print(f"   • Batches processed: {results['batches_completed']}")
        print(f"   • Total processing time: {total_time:.1f}s")
        print(f"   • Average per batch: {total_time/max(1, results['batches_completed']):.1f}s")
        print(f"   • Speed: {results['total_saved']/(total_time/60):.1f} tools/minute")
        
        return results
    
    def _discover_with_strategy(self, category: str, strategy: dict, db: Session):
        """Discovery with specific strategy"""
        from app.services.chat_service import parse_tools_from_response, enhance_pricing_info, save_discovered_tools_with_deduplication
        from app.services.agent_service import agent_service
        
        prompt = f"""CRITICAL: Return ONLY valid JSON array.

{strategy['prompt_suffix']} in category: {category.replace('_', ' ').title()}

Find 15 REAL tools. Requirements:
- Must exist with working websites
- AI/ML powered
- Include lesser-known alternatives

JSON format:
[{{"name":"Tool","website":"https://url.com","description":"What it does","tool_type":"{category}","category":"Subcategory","pricing":"Type","features":"List","confidence":0.9}}]"""
        
        try:
            ai_response = agent_service.send(prompt, block=True, timeout=90)
            tools = parse_tools_from_response(ai_response)
            
            if tools:
                enhanced_tools = enhance_pricing_info(tools)
                save_result = save_discovered_tools_with_deduplication(db, enhanced_tools)
                return {"success": True, "database_result": save_result}
            else:
                return {"success": False, "error": "No tools parsed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _discover_category_turbo(self, category: str, db: Session) -> Dict[str, Any]:
        """Optimized category discovery for turbo mode"""
        
        try:
            # Create enhanced prompt for turbo mode (request more tools)
            prompt = self._create_turbo_prompt(category)
            
            # Use existing discover_tools function but with optimized prompt
            from app.services.agent_service import agent_service
            from app.services.chat_service import parse_tools_from_response, enhance_pricing_info, save_discovered_tools_with_deduplication
            
            # Faster AI processing with shorter timeout
            ai_response = agent_service.send(prompt, block=True, timeout=75)
            tools = parse_tools_from_response(ai_response)
            
            if tools:
                # Fast enhancement (reduced processing for speed)
                enhanced_tools = self._turbo_enhance_pricing(tools)
                
                # Save with deduplication
                save_result = save_discovered_tools_with_deduplication(db, enhanced_tools)
                
                return {
                    "success": True,
                    "count": len(tools),
                    "database_result": save_result
                }
            else:
                return {"success": False, "error": "No tools parsed from response"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_turbo_prompt(self, category: str) -> str:
        """Create optimized prompts for turbo discovery mode"""
        
        category_descriptions = {
            "ai_writing_tools": "AI writing assistants, content creators, copywriting tools",
            "ai_image_generation": "AI image generators, art creation tools, design assistants",
            "ai_video_tools": "AI video creators, editors, animation tools",
            "ai_audio_tools": "AI music generators, voice synthesis, audio editing tools",
            "ai_coding_tools": "AI coding assistants, code completion, development tools",
            "ai_data_analysis": "AI data visualization, analytics platforms, BI tools",
            "ai_marketing_tools": "AI marketing automation, social media tools, SEO assistants",
            "ai_customer_service": "AI chatbots, customer support tools, help desk automation",
            "ai_hr_tools": "AI recruitment tools, HR automation, talent management",
            "ai_finance_tools": "AI trading platforms, financial analysis, accounting tools",
            "ai_education_tools": "AI tutoring platforms, learning tools, educational assistants",
            "ai_research_tools": "AI research assistants, academic helpers, citation tools",
            "ai_3d_modeling": "AI 3D generators, CAD tools, modeling assistants",
            "ai_gaming_tools": "AI game development tools, procedural generation",
            "desktop_applications": "Desktop software with AI features",
            "browser_extensions": "Browser extensions with AI capabilities",
            "mobile_apps": "Mobile applications with AI/ML features",
            "web_applications": "Web-based AI tools and SaaS platforms",
            "ai_services": "AI APIs and cloud services",
            "code_editors": "AI-powered IDEs and development environments",
            "plugins": "IDE plugins and development extensions",
            "creative_tools": "AI tools for creative work and design",
            "business_tools": "AI business automation and enterprise tools",
            "productivity_tools": "AI productivity apps and task management"
        }
        
        category_desc = category_descriptions.get(category, category.replace('_', ' ').title())
        
        # Optimized prompt for speed and volume
        prompt = f"""CRITICAL: Return ONLY valid JSON array. No explanations.

Find 18 REAL AI tools in: {category_desc}

Requirements:
- Must be real tools with working websites
- AI/ML as core feature
- Mix of popular and emerging tools
- Include free, freemium, and paid options

Return JSON array:
[
  {{
    "name": "Tool Name",
    "website": "https://website.com",
    "description": "What this tool does",
    "tool_type": "{category}",
    "category": "Subcategory",
    "pricing": "Free|Freemium|Paid",
    "features": "Feature1, Feature2, Feature3",
    "confidence": 0.9
  }}
]

Focus on real, existing tools only."""
        
        return prompt

    def _turbo_enhance_pricing(self, tools: List[dict]) -> List[dict]:
        """Fast pricing enhancement for turbo mode"""
        
        # Simplified pricing enhancement for speed
        for tool in tools:
            pricing = tool.get('pricing', 'Unknown').strip()
            
            # Quick standardization without heavy processing
            if pricing.lower() in ['free', 'open source', 'opensource', 'no cost']:
                tool['pricing'] = 'Free'
            elif pricing.lower() in ['freemium', 'free trial', 'free tier']:
                tool['pricing'] = 'Freemium'
            elif pricing.lower() in ['paid', 'premium', 'subscription', 'pro']:
                tool['pricing'] = 'Paid'
            elif pricing.lower() in ['enterprise', 'custom', 'contact sales']:
                tool['pricing'] = 'Enterprise'
            else:
                # Keep original if it doesn't match standard patterns
                tool['pricing'] = pricing
        
        return tools

# Global instance
discovery_pipeline = DiscoveryPipeline()