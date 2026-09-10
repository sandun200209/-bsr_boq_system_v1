from __future__ import annotations
from typing import Sequence
from ..models import RateItem, MasterItem
from ..schemas import CompareGroupOut, CompareRowOut, CompareResponse
from .validation_service import generate_comparison_key

class CompareService:
    @staticmethod
    def build_comparison(
        items: Sequence[RateItem],
        base_item_id: int | None = None,
    ) -> CompareResponse:
        """
        Groups matching rate items (by master_item_id if present, or by semantic comparison key)
        and computes LKR difference, percentage difference, min, max, and average rates.
        """
        groups_dict: dict[str, list[RateItem]] = {}
        group_meta: dict[str, dict] = {}

        for item in items:
            if item.rate is None or item.rate <= 0:
                continue

            if item.master_item_id and item.master_item:
                group_key = f"master_{item.master_item_id}"
                title = f"{item.master_item.canonical_description} [{item.master_item.master_code}]"
                unit = item.master_item.canonical_unit or item.unit
            else:
                # Strictly isolate unmapped items - never treat similar descriptions as identical
                group_key = f"unmapped_{item.id}"
                title = f"{item.description or item.item_code or 'Item'} (Unmapped item - Assign Master Item to compare)"
                unit = item.unit

            if group_key not in groups_dict:
                groups_dict[group_key] = []
                group_meta[group_key] = {"title": title, "unit": unit}

            groups_dict[group_key].append(item)

        compare_groups: list[CompareGroupOut] = []
        total_items_compared = 0

        for g_key, g_items in groups_dict.items():
            if not g_items:
                continue

            rates = [it.rate for it in g_items if it.rate is not None]
            min_rate = min(rates) if rates else 0.0
            max_rate = max(rates) if rates else 0.0
            avg_rate = round(sum(rates) / len(rates), 2) if rates else 0.0
            spread = round(max_rate - min_rate, 2)

            # Determine base item: requested ID, or first item in group
            selected_base = None
            if base_item_id:
                selected_base = next((it for it in g_items if it.id == base_item_id), None)
            if not selected_base:
                selected_base = g_items[0]

            base_rate = selected_base.rate if selected_base and selected_base.rate else (rates[0] if rates else 1.0)
            base_id = selected_base.id if selected_base else None

            rows: list[CompareRowOut] = []
            for it in g_items:
                it_rate = it.rate or 0.0
                is_base = (it.id == base_id)
                diff_lkr = round(it_rate - base_rate, 2)
                diff_pct = round(((it_rate - base_rate) / base_rate) * 100, 2) if base_rate > 0 else 0.0
                source_label = f"{it.source_file.original_filename if it.source_file else 'Source'} (p.{it.source_page or 1})"

                rows.append(
                    CompareRowOut(
                        id=it.id,
                        source_file_id=it.source_file_id,
                        province=it.province,
                        district=it.district,
                        year=it.year,
                        revision=it.revision,
                        category_name=it.category_name,
                        item_code=it.item_code,
                        description=it.description,
                        unit=it.unit,
                        rate=it_rate,
                        is_base=is_base,
                        diff_lkr=diff_lkr,
                        diff_percent=diff_pct,
                        source_label=source_label,
                    )
                )

            total_items_compared += len(rows)
            compare_groups.append(
                CompareGroupOut(
                    key=g_key,
                    title=group_meta[g_key]["title"],
                    unit=group_meta[g_key]["unit"],
                    base_item_id=base_id,
                    min_rate=min_rate,
                    max_rate=max_rate,
                    avg_rate=avg_rate,
                    spread=spread,
                    items=rows,
                )
            )

        return CompareResponse(
            groups=compare_groups,
            total_groups=len(compare_groups),
            total_items_compared=total_items_compared,
        )
