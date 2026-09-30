#include "BrawlerHUD.h"

#include "BrawlerAssets.h"
#include "BrawlerEnemy.h"
#include "BrawlerGameMode.h"
#include "BrawlerMenu.h"
#include "BrawlerPlayer.h"
#include "BrawlerSettings.h"
#include "BrawlerStageData.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	const FLinearColor Ink(0.02f, 0.015f, 0.03f, 1.f);
	const FLinearColor Yellow(1.f, 0.78f, 0.1f, 1.f);
	const FLinearColor Green(0.3f, 0.9f, 0.35f, 1.f);
	const FLinearColor RedBar(0.95f, 0.2f, 0.2f, 1.f);
	const FLinearColor White(1.f, 1.f, 1.f, 1.f);
	const FLinearColor Pink(1.f, 0.25f, 0.5f, 1.f);
	const FLinearColor Soft(0.81f, 0.78f, 0.88f, 1.f);
	const FLinearColor Dim(0.54f, 0.51f, 0.6f, 1.f);
}

void ABrawlerHUD::Rect(float X, float Y, float W, float H, const FLinearColor& Color)
{
	DrawRect(Color, OX + X * S, OY + Y * S, W * S, H * S);
}

void ABrawlerHUD::Text(const FString& Str, float X, float Y, float Scale, const FLinearColor& Color, bool bCenter, bool bRight)
{
	UFont* Font = GEngine ? GEngine->GetLargeFont() : nullptr;
	float W = 0.f, H = 0.f;
	GetTextSize(Str, W, H, Font, Scale * S);
	float PX = OX + X * S;
	if (bCenter)
	{
		PX -= W * 0.5f;
	}
	else if (bRight)
	{
		PX -= W;
	}
	const float PY = OY + Y * S;
	// Kontur fuer Lesbarkeit
	const float O = FMath::Max(1.f, 2.f * S);
	for (const FVector2D& D : { FVector2D(-O, 0.f), FVector2D(O, 0.f), FVector2D(0.f, -O), FVector2D(0.f, O), FVector2D(O, O) })
	{
		DrawText(Str, Ink, PX + D.X, PY + D.Y, Font, Scale * S);
	}
	DrawText(Str, Color, PX, PY, Font, Scale * S);
}

void ABrawlerHUD::Tex(UTexture2D* Texture, float X, float Y, float W, float H, float Alpha)
{
	if (Texture)
	{
		DrawTexture(Texture, OX + X * S, OY + Y * S, W * S, H * S, 0.f, 0.f, 1.f, 1.f, FLinearColor(1.f, 1.f, 1.f, Alpha));
	}
}

void ABrawlerHUD::Bar(float X, float Y, float W, float H, float Value, float Recoverable, const FLinearColor& Color, bool bRightToLeft)
{
	Rect(X - 4.f, Y - 4.f, W + 8.f, H + 8.f, Ink);
	Rect(X, Y, W, H, FLinearColor(0.18f, 0.12f, 0.16f, 1.f));
	const float V = FMath::Clamp(Value, 0.f, 1.f);
	const float R = FMath::Clamp(Value + Recoverable, 0.f, 1.f);
	if (bRightToLeft)
	{
		Rect(X + W * (1.f - R), Y, W * R, H, Green);
		Rect(X + W * (1.f - V), Y, W * V, H, Color);
	}
	else
	{
		Rect(X, Y, W * R, H, Green);
		Rect(X, Y, W * V, H, Color);
	}
	// Glanzlinie
	Rect(X, Y + 2.f, W, 3.f, FLinearColor(1.f, 1.f, 1.f, 0.25f));
}

void ABrawlerHUD::FighterPanel(ABrawlerFighter* Fighter, bool bRightSide, float Recoverable)
{
	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	UTexture2D* Portrait = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("Portrait_") + Fighter->SpriteSet) : nullptr;

	const float PortraitSize = 96.f;
	const float BarW = 400.f;
	const float PX = bRightSide ? 1600.f - 24.f - PortraitSize : 24.f;
	Rect(PX - 4.f, 14.f, PortraitSize + 8.f, PortraitSize + 8.f, Ink);
	Rect(PX, 18.f, PortraitSize, PortraitSize, bRightSide ? FLinearColor(0.35f, 0.1f, 0.15f, 1.f) : FLinearColor(0.1f, 0.2f, 0.4f, 1.f));
	Tex(Portrait, PX, 18.f, PortraitSize, PortraitSize);

	const float BX = bRightSide ? PX - 16.f - BarW : PX + PortraitSize + 16.f;
	Text(Fighter->DisplayName, bRightSide ? BX + BarW : BX, 16.f, 1.1f, White, false, bRightSide);
	const float HealthFrac = Fighter->Health / FMath::Max(1.f, Fighter->MaxHealth);
	Bar(BX, 52.f, BarW, 22.f, HealthFrac, Recoverable / FMath::Max(1.f, Fighter->MaxHealth), bRightSide ? RedBar : Yellow, bRightSide);
}

void ABrawlerHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas)
	{
		return;
	}

	S = FMath::Min(Canvas->ClipX / 1600.f, Canvas->ClipY / 900.f);
	OX = (Canvas->ClipX - 1600.f * S) * 0.5f;
	OY = (Canvas->ClipY - 900.f * S) * 0.5f;

	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (!GM)
	{
		return;
	}
	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	const float T = GM->GetFlowTime();
	const bool bBlink = FMath::Fmod(GetWorld()->GetRealTimeSeconds(), 0.8f) < 0.5f;

	if (GM->GetFlow() == EBrawlerFlow::Title)
	{
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, 0.55f));
		const FMenuLevel* Top = GM->GetMenu() ? GM->GetMenu()->Top() : nullptr;
		if (Top && Top->Screen == EMenuScreen::Main)
		{
			UTexture2D* Logo = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("UI_Logo")) : nullptr;
			if (Logo)
			{
				Tex(Logo, 250.f, 90.f, 1100.f, 300.f);
			}
			else
			{
				Text(TEXT("STREETS OF BERLIN"), 800.f, 200.f, 3.f, Yellow, true);
			}
		}
		DrawMenu(GM);
		return;
	}

	// --- Spieler-Panel -----------------------------------------------------
	if (ABrawlerPlayer* Player = GM->GetPlayer())
	{
		FighterPanel(Player, false, Player->GetRecoverableHealth());
		Text(FString::Printf(TEXT("x%d"), FMath::Max(0, GM->GetLives() - 1)), 30.f, 118.f, 1.1f, Yellow);
		Text(FString::Printf(TEXT("%07d"), GM->GetScore()), 136.f, 84.f, 1.1f, White);
		if (Player->HasWeapon())
		{
			if (const FWeaponDef* W = BrawlerData::GetWeapon(Player->GetWeapon()))
			{
				Text(FString::Printf(TEXT("%s x%d"), *W->DisplayName, Player->GetWeaponDurability()), 552.f, 50.f, 0.9f, FLinearColor(0.6f, 0.9f, 1.f, 1.f));
			}
		}
	}

	// --- Gegner-Panel ------------------------------------------------------
	ABrawlerFighter* Enemy = GM->GetLastHitEnemy();
	if (Enemy && (GM->GetLastHitEnemyTimer() > 0.f || (GM->IsBossFight() && Cast<ABrawlerEnemy>(Enemy) && Cast<ABrawlerEnemy>(Enemy)->IsBoss())))
	{
		FighterPanel(Enemy, true, 0.f);
	}

	// --- Combo ---------------------------------------------------------------
	if (GM->GetComboHits() >= 2 && GM->GetComboTimer() > 0.f)
	{
		const float Pop = 1.f + FMath::Clamp(GM->GetComboTimer() - 1.2f, 0.f, 0.2f) * 2.f;
		Text(FString::Printf(TEXT("%d"), GM->GetComboHits()), 40.f, 170.f, 2.6f * Pop, Yellow);
		Text(TEXT("HITS"), 40.f, 240.f, 1.1f, White);
	}

	// --- GO-Pfeil ------------------------------------------------------------
	if (GM->GetGoArrowTimer() > 0.f && bBlink)
	{
		UTexture2D* Go = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("UI_Go")) : nullptr;
		if (Go)
		{
			Tex(Go, 1360.f, 360.f, 200.f, 110.f);
		}
		else
		{
			Text(TEXT("GO ->"), 1450.f, 380.f, 2.f, Yellow, true);
		}
	}

	// --- Ablauf-Texte --------------------------------------------------------
	switch (GM->GetFlow())
	{
	case EBrawlerFlow::Intro:
		Text(GM->GetStageDef().Name, 800.f, 330.f, 2.2f, Yellow, true);
		Text(GM->GetStageDef().Title, 800.f, 400.f, 1.6f, White, true);
		break;
	case EBrawlerFlow::StageClear:
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, FMath::Clamp(T * 0.3f, 0.f, 0.5f)));
		Text(GM->GetStageDef().Name + TEXT(" CLEAR!"), 800.f, 300.f, 3.f, Yellow, true);
		Text(FString::Printf(TEXT("PUNKTE: %d"), GM->GetScore()), 800.f, 420.f, 1.6f, White, true);
		if (T > 2.f && bBlink)
		{
			Text(GM->GetStageIndex() + 1 < GM->GetStageCount() ? TEXT("ENTER / START: WEITER") : TEXT("ENTER / START"), 800.f, 520.f, 1.2f, White, true);
		}
		break;
	case EBrawlerFlow::Ending:
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, 0.7f));
		Text(TEXT("BERLIN IST GERETTET!"), 800.f, 260.f, 2.6f, Yellow, true);
		Text(TEXT("Harald Immobilien ist pleite - die Mieten bleiben bezahlbar."), 800.f, 360.f, 1.2f, White, true);
		Text(FString::Printf(TEXT("ENDPUNKTE: %d"), GM->GetScore()), 800.f, 440.f, 1.6f, White, true);
		if (T > 1.5f && bBlink)
		{
			Text(TEXT("ENTER / START: TITEL"), 800.f, 540.f, 1.2f, White, true);
		}
		break;
	case EBrawlerFlow::GameOver:
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, FMath::Clamp(T * 0.4f, 0.f, 0.65f)));
		Text(TEXT("GAME OVER"), 800.f, 320.f, 3.2f, Pink, true);
		if (T > 1.5f && bBlink)
		{
			Text(TEXT("ENTER / START: NOCHMAL"), 800.f, 470.f, 1.2f, White, true);
		}
		break;
	default:
		break;
	}

	DrawMenu(GM);
}

// ---------------------------------------------------------------------------
// Menues
// ---------------------------------------------------------------------------
void ABrawlerHUD::Frame(float X, float Y, float W, float H, float T, const FLinearColor& Color)
{
	Rect(X, Y, W, T, Color);
	Rect(X, Y + H - T, W, T, Color);
	Rect(X, Y, T, H, Color);
	Rect(X + W - T, Y, T, H, Color);
}

void ABrawlerHUD::Highlight(float X, float Y, float W, float H)
{
	const float Pulse = 0.55f + 0.25f * FMath::Sin(GetWorld()->GetRealTimeSeconds() * 6.f);
	Rect(X, Y, W, H, FLinearColor(1.f, 0.24f, 0.59f, 0.22f * Pulse + 0.1f));
	Rect(X, Y, 8.f, H, Pink);
}

void ABrawlerHUD::DrawMenu(ABrawlerGameMode* GM)
{
	UBrawlerMenu* Menu = GM->GetMenu();
	const FMenuLevel* Top = Menu ? Menu->Top() : nullptr;
	if (!Top)
	{
		return;
	}
	if (Top->Screen != EMenuScreen::Main)
	{
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.02f, 0.015f, 0.05f, 0.75f));
	}
	switch (Top->Screen)
	{
	case EMenuScreen::Select: DrawCharacterSelect(Menu); break;
	case EMenuScreen::Controls: DrawControls(Menu); break;
	default: DrawMenuList(Menu); break;
	}
}

FString ABrawlerHUD::ControlsHint(UBrawlerMenu* Menu) const
{
	const UBrawlerSettings* Set = Menu->GetSettings();
	if (!Set)
	{
		return FString();
	}
	const auto K = [Set](EBrawlerAction A)
	{
		const FKey Key = Set->GetKey(A, 0).IsValid() ? Set->GetKey(A, 0) : Set->GetKey(A, 1);
		return UBrawlerSettings::KeyLabel(Key);
	};
	return FString::Printf(TEXT("Laufen %s %s %s %s    Schlag %s    Sprung %s    Spezial %s    Rückschlag %s"),
		*K(EBrawlerAction::Up), *K(EBrawlerAction::Left), *K(EBrawlerAction::Down), *K(EBrawlerAction::Right),
		*K(EBrawlerAction::Attack), *K(EBrawlerAction::Jump), *K(EBrawlerAction::Special), *K(EBrawlerAction::Back));
}

void ABrawlerHUD::DrawMenuList(UBrawlerMenu* Menu)
{
	const FMenuLevel& L = *Menu->Top();
	const bool bMain = L.Screen == EMenuScreen::Main;
	const bool bWide = L.Screen == EMenuScreen::Options;
	if (L.Screen == EMenuScreen::Pause)
	{
		Text(TEXT("PAUSE"), 800.f, 150.f, 2.6f, Yellow, true);
	}
	else if (L.Screen == EMenuScreen::Options)
	{
		Text(TEXT("OPTIONEN"), 800.f, 150.f, 2.6f, Yellow, true);
	}
	const float Y0 = bMain ? 440.f : 280.f;
	const float Step = bMain ? 70.f : 78.f;
	const float W = bWide ? 900.f : 560.f;
	const float X = 800.f - W * 0.5f;
	const int32 Count = Menu->GetItemCount(L.Screen);
	for (int32 I = 0; I < Count; ++I)
	{
		const float Y = Y0 + I * Step;
		const bool bSel = I == L.Sel;
		if (bSel)
		{
			Highlight(X, Y - 8.f, W, Step - 12.f);
		}
		const FLinearColor Col = Menu->IsItemDimmed(L.Screen, I) ? Dim : (bSel ? Yellow : White);
		const FString Value = Menu->GetItemValue(L.Screen, I);
		if (!Value.IsEmpty())
		{
			Text(Menu->GetItemLabel(L.Screen, I), X + 30.f, Y, 1.3f, Col);
			const float VX = X + W - 150.f;
			Text(TEXT("<"), VX - 110.f, Y, 1.3f, bSel ? Pink : Dim, true);
			Text(Value, VX, Y, 1.3f, Col, true);
			Text(TEXT(">"), VX + 110.f, Y, 1.3f, bSel ? Pink : Dim, true);
		}
		else
		{
			Text(Menu->GetItemLabel(L.Screen, I), 800.f, Y, bMain ? 1.6f : 1.4f, Col, true);
		}
	}
	if (bMain)
	{
		Text(ControlsHint(Menu), 800.f, 690.f, 0.9f, Soft, true);
		Text(TEXT("In Gegner hineinlaufen = Griff  ->  Schlag = Knie,  weg + Schlag = Wurf"), 800.f, 730.f, 0.9f, Soft, true);
		Text(TEXT("3 Stages: Kreuzberg - East Side Gallery - Baustelle am Alex"), 800.f, 770.f, 0.9f, Yellow, true);
	}
	else
	{
		Text(TEXT("HOCH/RUNTER WÄHLEN    LINKS/RECHTS ÄNDERN    ENTER / A: OK    ESC / B: ZURÜCK"), 800.f, 830.f, 0.9f, Soft, true);
	}
}

void ABrawlerHUD::DrawControls(UBrawlerMenu* Menu)
{
	const FMenuLevel& L = *Menu->Top();
	const UBrawlerSettings* Set = Menu->GetSettings();
	Text(TEXT("STEUERUNG"), 800.f, 60.f, 2.3f, Yellow, true);
	const float Cols[3] = { 800.f, 1040.f, 1280.f };
	const float ColW = 220.f, X0 = 220.f, Y0 = 190.f, Step = 50.f;
	Text(TEXT("AKTION"), X0 + 20.f, 140.f, 0.9f, Soft);
	Text(TEXT("TASTE 1"), Cols[0], 140.f, 0.9f, Soft, true);
	Text(TEXT("TASTE 2"), Cols[1], 140.f, 0.9f, Soft, true);
	Text(TEXT("GAMEPAD"), Cols[2], 140.f, 0.9f, Soft, true);
	const int32 Count = Menu->GetItemCount(EMenuScreen::Controls);
	for (int32 I = 0; I < Count; ++I)
	{
		const float Y = Y0 + I * Step;
		const bool bSel = I == L.Sel;
		const int32 Action = Menu->GetControlsAction(I);
		if (Action != INDEX_NONE && Set)
		{
			if (bSel)
			{
				Highlight(X0, Y - 6.f, 1180.f, Step - 6.f);
			}
			Text(Menu->GetItemLabel(EMenuScreen::Controls, I), X0 + 20.f, Y, 1.1f, bSel ? Yellow : White);
			for (int32 C = 0; C < 3; ++C)
			{
				const bool bWaiting = Menu->IsWaiting() && Menu->GetWaitAction() == Action && Menu->GetWaitSlot() == C;
				const FString Val = bWaiting ? FString(C == UBrawlerSettings::PadSlot ? TEXT("KNOPF ...") : TEXT("TASTE ..."))
					: UBrawlerSettings::KeyLabel(Set->GetKey(static_cast<EBrawlerAction>(Action), C));
				if (bSel && L.Col == C)
				{
					Frame(Cols[C] - ColW * 0.5f, Y - 6.f, ColW, Step - 6.f, 3.f, bWaiting ? Yellow : Pink);
				}
				Text(Val, Cols[C], Y, 1.f, bWaiting ? Yellow : White, true);
			}
		}
		else
		{
			const float YY = Y + 14.f;
			if (bSel)
			{
				Highlight(500.f, YY - 6.f, 600.f, Step - 6.f);
			}
			Text(Menu->GetItemLabel(EMenuScreen::Controls, I), 800.f, YY, 1.2f, bSel ? Yellow : White, true);
		}
	}
	const TCHAR* Hint = !Menu->IsWaiting() ? TEXT("HOCH/RUNTER AKTION    LINKS/RECHTS SPALTE    ENTER NEU BELEGEN    ESC ZURÜCK")
		: (Menu->GetWaitSlot() == UBrawlerSettings::PadSlot ? TEXT("GAMEPAD-KNOPF DRÜCKEN  -  ESC ABBRECHEN")
			: TEXT("NEUE TASTE DRÜCKEN  -  RÜCKTASTE LEEREN  -  ESC ABBRECHEN"));
	Text(Hint, 800.f, 820.f, 0.9f, Menu->IsWaiting() ? Yellow : Soft, true);
	Text(TEXT("Belegte Tasten werden getauscht. Menüs: Pfeile, Enter und Esc funktionieren immer."), 800.f, 858.f, 0.75f, Dim, true);
}

void ABrawlerHUD::DrawCharacterSelect(UBrawlerMenu* Menu)
{
	const FMenuLevel& L = *Menu->Top();
	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	const TArray<FPlayerProfile>& Profiles = ABrawlerPlayer::GetProfiles();
	Text(TEXT("WÄHLE DEINE FIGUR"), 800.f, 60.f, 2.3f, Yellow, true);
	const float CW = 440.f, CH = 470.f, Y = 150.f;
	for (int32 I = 0; I < Profiles.Num(); ++I)
	{
		const FPlayerProfile& P = Profiles[I];
		const bool bSel = I == L.Sel;
		const float CX = 800.f + (I - (Profiles.Num() - 1) * 0.5f) * 480.f;
		const float X = CX - CW * 0.5f;
		Rect(X - 5.f, Y - 5.f, CW + 10.f, CH + 10.f, Ink);
		Rect(X, Y, CW, CH, bSel ? (I ? FLinearColor(0.29f, 0.12f, 0.43f, 1.f) : FLinearColor(0.12f, 0.23f, 0.48f, 1.f)) : FLinearColor(0.13f, 0.1f, 0.18f, 1.f));
		if (bSel)
		{
			Frame(X, Y, CW, CH, 5.f, Pink);
		}
		UTexture2D* Portrait = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("Portrait_") + P.SpriteSet) : nullptr;
		Tex(Portrait, CX - 150.f, Y + 80.f, 300.f, 300.f, bSel ? 1.f : 0.5f);
		Text(P.DisplayName, CX, Y + 16.f, 1.8f, bSel ? Yellow : Soft, true);
		const TPair<const TCHAR*, int32> Stats[3] = { { TEXT("KRAFT"), P.Power }, { TEXT("TEMPO"), P.Speed }, { TEXT("REICHWEITE"), P.Reach } };
		for (int32 J = 0; J < 3; ++J)
		{
			const float SY = Y + 400.f + J * 22.f;
			Text(Stats[J].Key, X + 24.f, SY - 4.f, 0.6f, Soft);
			for (int32 B = 0; B < 5; ++B)
			{
				Rect(X + 170.f + B * 48.f, SY, 42.f, 12.f, B < Stats[J].Value ? (bSel ? Yellow : Dim) : FLinearColor(0.18f, 0.14f, 0.22f, 1.f));
			}
		}
	}
	if (Profiles.IsValidIndex(L.Sel))
	{
		const TArray<FString>& Desc = Profiles[L.Sel].Description;
		for (int32 I = 0; I < Desc.Num(); ++I)
		{
			Text(Desc[I], 800.f, 650.f + I * 38.f, I ? 1.f : 1.15f, I ? White : Yellow, true);
		}
	}
	Text(TEXT("LINKS/RECHTS WÄHLEN    ENTER / A: LOS!    ESC / B: ZURÜCK"), 800.f, 838.f, 0.9f, Soft, true);
}
